<?php

class Router {
    private array $routes = [];

    public function get(string $path, callable $handler): self {
        $this->routes['GET'][$path] = $handler;
        return $this;
    }

    public function post(string $path, callable $handler): self {
        $this->routes['POST'][$path] = $handler;
        return $this;
    }

    public function dispatch(string $method, string $uri): ?string {
        $handler = $this->routes[$method][$uri] ?? null;
        if ($handler === null) {
            return null;
        }
        return $handler();
    }
}

class JsonResponse {
    public static function create(array $data, int $status = 200): string {
        http_response_code($status);
        header('Content-Type: application/json');
        return json_encode($data);
    }
}

$router = new Router();

$router->get('/api/users', function () {
    $users = [
        ['id' => 1, 'name' => 'Alice'],
        ['id' => 2, 'name' => 'Bob'],
    ];
    return JsonResponse::create(['users' => $users]);
});

$router->post('/api/users', function () {
    return JsonResponse::create(['created' => true], 201);
});

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$uri = $_SERVER['REQUEST_URI'] ?? '/';
$response = $router->dispatch($method, $uri);

if ($response === null) {
    echo JsonResponse::create(['error' => 'Not Found'], 404);
} else {
    echo $response;
}
