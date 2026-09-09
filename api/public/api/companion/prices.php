<?php

declare(strict_types=1);

require dirname(__DIR__, 3) . '/config/bootstrap.php';

const COMPANION_MAX_BODY_BYTES = 16384;
const COMPANION_RATE_LIMIT_PER_MINUTE = 200;
const COMPANION_MAX_PRICE = 9007199254740991;
const COMPANION_MAX_QUANTITY = 1000000;

function companionResponse(array $payload, int $status = 200): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store, max-age=0');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    exit;
}

function companionPositiveInt(array $payload, string $key, int $maximum): int
{
    $value = $payload[$key] ?? null;

    if (!is_int($value) && !(is_string($value) && preg_match('/^[1-9][0-9]*$/D', $value))) {
        companionResponse(['ok' => false, 'error' => "Champ {$key} invalide."], 422);
    }

    $integer = filter_var($value, FILTER_VALIDATE_INT, [
        'options' => ['min_range' => 1, 'max_range' => $maximum],
    ]);

    if ($integer === false) {
        companionResponse(['ok' => false, 'error' => "Champ {$key} hors limites."], 422);
    }

    return (int)$integer;
}

function companionCapturedAt(array $payload): DateTimeImmutable
{
    $timestamp = companionPositiveInt($payload, 'captured_at', PHP_INT_MAX);
    $capturedAt = (new DateTimeImmutable('@' . $timestamp))->setTimezone(new DateTimeZone('UTC'));
    $now = new DateTimeImmutable('now', new DateTimeZone('UTC'));

    if ($capturedAt < $now->modify('-7 days') || $capturedAt > $now->modify('+5 minutes')) {
        companionResponse(['ok' => false, 'error' => 'Date de capture incohérente.'], 422);
    }

    return $capturedAt;
}

function companionRiskScore(?int $previousPrice, int $newPrice): float
{
    if ($previousPrice === null || $previousPrice <= 0) {
        return 0.0;
    }

    $ratio = $newPrice / $previousPrice;

    if ($ratio >= 10.0 || $ratio <= 0.10) {
        return 80.0;
    }

    if ($ratio >= 3.0 || $ratio <= (1 / 3)) {
        return 40.0;
    }

    return 0.0;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    companionResponse(['ok' => false, 'error' => 'Méthode non autorisée.'], 405);
}

$contentLength = (int)($_SERVER['CONTENT_LENGTH'] ?? 0);
if ($contentLength > COMPANION_MAX_BODY_BYTES) {
    companionResponse(['ok' => false, 'error' => 'Corps de requête trop volumineux.'], 413);
}

$rawBody = file_get_contents('php://input', false, null, 0, COMPANION_MAX_BODY_BYTES + 1);
if ($rawBody === false || $rawBody === '' || strlen($rawBody) > COMPANION_MAX_BODY_BYTES) {
    companionResponse(['ok' => false, 'error' => 'Corps JSON manquant ou trop volumineux.'], 400);
}

try {
    $payload = json_decode($rawBody, true, 32, JSON_THROW_ON_ERROR);
} catch (JsonException) {
    companionResponse(['ok' => false, 'error' => 'JSON invalide.'], 400);
}

if (!is_array($payload) || array_is_list($payload)) {
    companionResponse(['ok' => false, 'error' => 'Objet JSON attendu.'], 400);
}

$allowedKeys = [
    'event_id',
    'device_id',
    'server_id',
    'item_id',
    'price',
    'quantity',
    'source',
    'transaction_confirmed',
    'captured_at',
];
$unknownKeys = array_diff(array_keys($payload), $allowedKeys);
if ($unknownKeys !== []) {
    companionResponse(['ok' => false, 'error' => 'Champ JSON inconnu.', 'fields' => array_values($unknownKeys)], 422);
}

$deviceId = $payload['device_id'] ?? null;
if (!is_string($deviceId) || !preg_match('/^[a-f0-9-]{36}$/D', $deviceId)) {
    companionResponse(['ok' => false, 'error' => 'device_id invalide.'], 422);
}
$deviceHash = hash('sha256', $deviceId);
$serverId = companionPositiveInt($payload, 'server_id', 4294967295);
$itemId = companionPositiveInt($payload, 'item_id', PHP_INT_MAX);
$rawPrice = $payload['price'] ?? null;

if ($rawPrice === 0 || $rawPrice === '0') {
    companionResponse([
        'ok' => true,
        'ignored' => true,
        'reason' => 'no_unit_offer',
    ]);
}

$price = companionPositiveInt(
    $payload,
    'price',
    COMPANION_MAX_PRICE
);

$quantity = companionPositiveInt(
    $payload,
    'quantity',
    COMPANION_MAX_QUANTITY
);

$capturedAt = companionCapturedAt($payload);
$source = $payload['source'] ?? null;


if (!is_string($source) || !in_array($source, ['astrub_companion', 'companion_purchase', 'companion_price_update', 'companion_market_view'], true)) {
    companionResponse(['ok' => false, 'error' => 'Source invalide.'], 422);
}

$eventKind = match ($source) {
    'companion_purchase' => 'purchase',
    'companion_price_update' => 'price_update',
    'companion_market_view' => 'market_view',
    default => 'listing',
};
$objectUid = null;
$offerId = null;

if ($eventKind === 'purchase') {
    if (($payload['transaction_confirmed'] ?? null) !== true) {
        companionResponse(['ok' => false, 'error' => 'Achat confirmé invalide.'], 422);
    }
}

if ($eventKind === 'price_update') {
    if (($payload['transaction_confirmed'] ?? null) !== true) {
        companionResponse(['ok' => false, 'error' => 'Modification de prix confirmée invalide.'], 422);
    }
}

if ($eventKind === 'market_view') {
    if (($payload['transaction_confirmed'] ?? null) !== true) {
        companionResponse(['ok' => false, 'error' => 'Observation HDV confirmée invalide.'], 422);
    }
}

$eventId = $payload['event_id'] ?? null;
if (!is_string($eventId) || !preg_match('/^[a-f0-9-]{36}$/D', $eventId)) {
    companionResponse(['ok' => false, 'error' => 'event_id invalide.'], 422);
}

$pdo = db();
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

if ($quantity !== 1) {
    companionResponse([
        'ok' => true,
        'ignored' => true,
        'reason' => 'quantity_not_one',
        'quantity' => $quantity,
    ]);
}

$fingerprintMaterial = 'anonymous-event|' . $deviceHash . '|' . $eventId;
$fingerprint = hash('sha256', $fingerprintMaterial);

$duplicateStatement = $pdo->prepare(
    'SELECT id FROM companion_price_events WHERE event_fingerprint = UNHEX(:fingerprint) LIMIT 1'
);
$duplicateStatement->execute(['fingerprint' => $fingerprint]);
$duplicateId = $duplicateStatement->fetchColumn();

if ($duplicateId !== false) {
    companionResponse(['ok' => true, 'duplicate' => true, 'event_id' => (int)$duplicateId]);
}

$rateStatement = $pdo->prepare(
    'SELECT COUNT(*) FROM companion_price_events WHERE device_hash = UNHEX(:device_hash) AND received_at >= UTC_TIMESTAMP() - INTERVAL 1 MINUTE'
);
$rateStatement->execute(['device_hash' => $deviceHash]);
if ((int)$rateStatement->fetchColumn() >= COMPANION_RATE_LIMIT_PER_MINUTE) {
    header('Retry-After: 60');
    companionResponse(['ok' => false, 'error' => 'Trop de contributions. Réessayez plus tard.'], 429);
}

$serverStatement = $pdo->prepare('SELECT id FROM servers WHERE id = :id AND is_active = 1 LIMIT 1');
$serverStatement->execute(['id' => $serverId]);
if ($serverStatement->fetchColumn() === false) {
    companionResponse(['ok' => false, 'error' => 'Serveur invalide ou inactif.'], 422);
}

$itemStatement = $pdo->prepare('SELECT ankama_id, name__fr FROM MAPPED_ITEMS WHERE ankama_id = :id LIMIT 1');
$itemStatement->execute(['id' => $itemId]);
$item = $itemStatement->fetch(PDO::FETCH_ASSOC);
if (!$item) {
    companionResponse(['ok' => false, 'error' => 'Objet Ankama inconnu.'], 422);
}

$userAgent = substr((string)($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 190);

try {
    $pdo->beginTransaction();

    $currentStatement = $pdo->prepare(
        'SELECT price FROM current_prices WHERE item_id = :item_id AND server_id = :server_id FOR UPDATE'
    );
    $currentStatement->execute(['item_id' => $itemId, 'server_id' => $serverId]);
    $previousValue = $currentStatement->fetchColumn();
    $previousPrice = $previousValue === false ? null : (int)$previousValue;
    $riskScore = companionRiskScore($previousPrice, $price);

    $eventStatement = $pdo->prepare(
        "INSERT INTO companion_price_events
            (token_id, user_id, device_hash, server_id, item_id, price, quantity, event_kind,
             object_uid, offer_id, event_uuid, event_fingerprint, captured_at,
             remote_ip, user_agent)
         VALUES
            (NULL, NULL, UNHEX(:device_hash), :server_id, :item_id, :price, :quantity, :event_kind,
             :object_uid, :offer_id, :event_uuid, UNHEX(:fingerprint), :captured_at,
             NULL, :user_agent)"
    );
    $eventStatement->execute([
        'device_hash' => $deviceHash,
        'server_id' => $serverId,
        'item_id' => $itemId,
        'price' => $price,
        'quantity' => $quantity,
        'event_kind' => $eventKind,
        'object_uid' => $objectUid,
        'offer_id' => $offerId,
        'event_uuid' => $eventId,
        'fingerprint' => $fingerprint,
        'captured_at' => $capturedAt->format('Y-m-d H:i:s'),
        'user_agent' => $userAgent,
    ]);
    $storedEventId = (int)$pdo->lastInsertId();

    $submissionStatement = $pdo->prepare(
        "INSERT INTO price_submissions
            (item_id, server_id, proposed_price, previous_price, submitted_by,
             contributor_ip_id, risk_score, status)
         VALUES (:item_id, :server_id, :price, :previous_price, NULL, NULL, :risk_score, 'accepted')"
    );
    $submissionStatement->execute([
        'item_id' => $itemId,
        'server_id' => $serverId,
        'price' => $price,
        'previous_price' => $previousPrice,
        'risk_score' => $riskScore,
    ]);

    $upsertStatement = $pdo->prepare(
        "INSERT INTO current_prices (item_id, server_id, price, updated_by, updated_ip_id, updated_at)
         VALUES (:item_id, :server_id, :price, NULL, NULL, UTC_TIMESTAMP())
         ON DUPLICATE KEY UPDATE
             price = VALUES(price),
             updated_by = VALUES(updated_by),
             updated_ip_id = NULL,
             updated_at = UTC_TIMESTAMP()"
    );
    $upsertStatement->execute([
        'item_id' => $itemId,
        'server_id' => $serverId,
        'price' => $price,
    ]);

    if ($previousPrice === null || $previousPrice !== $price) {
        $historyStatement = $pdo->prepare(
            "INSERT INTO price_history
                (item_id, server_id, price, changed_by, changed_ip_id, source, recorded_at)
             VALUES (:item_id, :server_id, :price, NULL, NULL, 'update', UTC_TIMESTAMP())"
        );
        $historyStatement->execute([
            'item_id' => $itemId,
            'server_id' => $serverId,
            'price' => $price,
        ]);
    }

    $pdo->commit();
} catch (PDOException $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    if ((string)$exception->getCode() === '23000') {
        $duplicateStatement->execute(['fingerprint' => $fingerprint]);
        $duplicateId = $duplicateStatement->fetchColumn();
        if ($duplicateId !== false) {
            companionResponse(['ok' => true, 'duplicate' => true, 'event_id' => (int)$duplicateId]);
        }
    }

    error_log('Astrub Companion API: ' . $exception->getMessage());
    companionResponse(['ok' => false, 'error' => 'Erreur interne.'], 500);
}

companionResponse([
    'ok' => true,
    'duplicate' => false,
    'event_id' => $storedEventId,
    'item_id' => $itemId,
    'item_name' => $item['name__fr'],
    'server_id' => $serverId,
    'price' => $price,
    'kind' => $eventKind,
]);
