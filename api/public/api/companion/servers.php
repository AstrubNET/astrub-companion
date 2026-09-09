<?php
declare(strict_types=1);

require dirname(__DIR__, 3) . '/config/bootstrap.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: public, max-age=300');
header('X-Content-Type-Options: nosniff');

$rows = db()->query('SELECT id, name FROM servers WHERE is_active = 1 ORDER BY name')->fetchAll(PDO::FETCH_ASSOC);
$servers = array_map(static fn(array $row): array => [
    'id' => (int)$row['id'],
    'name' => (string)$row['name'],
], $rows);

echo json_encode(['servers' => $servers], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
