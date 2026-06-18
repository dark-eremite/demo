# Инструкция по запуску Kubernetes для приложения Стройматериалы

## Предварительные требования

### 1. Установите необходимые инструменты:

**Для локальной разработки:**
- **Docker Desktop** (включает Kubernetes) или **Minikube** или **Kind**
- **kubectl** - CLI инструмент для управления Kubernetes
- **Helm** (опционально, для управления пакетами)

**Установка Minikube (рекомендуется для локальной разработки):**
```bash
# macOS
brew install minikube kubectl

# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Windows (через Chocolatey)
choco install minikube kubectl
```

### 2. Запустите локальный кластер:

```bash
# Запуск Minikube с достаточными ресурсами
minikube start --memory=4096 --cpus=2 --disk-size=20gb

# Проверка статуса
minikube status
```

## Развертывание приложения

### Шаг 1: Сборка Docker образов

```bash
# Соберите образ Django
docker build -t stroymaterials-django:latest .

# Соберите образ Nginx (предполагается, что есть Dockerfile в папке nginx/)
docker build -t stroymaterials-nginx:latest ./nginx
```

### Шаг 2: Загрузка образов в Minikube

```bash
# Для Minikube
eval $(minikube docker-env)
docker build -t stroymaterials-django:latest .
docker build -t stroymaterials-nginx:latest ./nginx
```

### Шаг 3: Применение манифестов Kubernetes

```bash
# Примените все манифесты по порядку
kubectl apply -f k8s-manifests/configmaps/
kubectl apply -f k8s-manifests/secrets/
kubectl apply -f k8s-manifests/pvcs/
kubectl apply -f k8s-manifests/deployments/
kubectl apply -f k8s-manifests/services/
kubectl apply -f k8s-manifests/ingress/

# Или применить все сразу
kubectl apply -R -f k8s-manifests/
```

### Шаг 4: Проверка статуса развертывания

```bash
# Проверка подов
kubectl get pods

# Проверка сервисов
kubectl get services

# Проверка деплойментов
kubectl get deployments

# Просмотр логов Django
kubectl logs -l app=django

# Просмотр логов PostgreSQL
kubectl logs -l app=postgres
```

### Шаг 5: Доступ к приложению

```bash
# Для Minikube - открыть приложение в браузере
minikube service nginx-service --url

# Или получить URL
minikube service nginx-service
```

## Управление приложением

### Масштабирование

```bash
# Увеличить количество реплик Django
kubectl scale deployment django-deployment --replicas=5

# Уменьшить количество реплик
kubectl scale deployment django-deployment --replicas=2
```

### Обновление приложения

```bash
# Пересобрать и обновить образ
docker build -t stroymaterials-django:latest .
kubectl rollout restart deployment django-deployment

# Отслеживание статуса обновления
kubectl rollout status deployment django-deployment
```

### Выполнение миграций вручную

```bash
# Запустить pod для выполнения команд
kubectl run django-migrate --image=stroymaterials-django:latest --rm -it --restart=Never -- python manage.py migrate
```

### Импорт данных

```bash
# Запустить job импорта данных
kubectl apply -f k8s-manifests/jobs/import-data-job.yaml

# Проверить статус job
kubectl get jobs
kubectl logs job/import-data-job
```

## Мониторинг и отладка

### Просмотр логов

```bash
# Логи всех подов с меткой app=django
kubectl logs -l app=django

# Логи в реальном времени
kubectl logs -l app=django -f

# Логи конкретного пода
kubectl logs <pod-name>
```

### Подключение к контейнеру

```bash
# Подключиться к контейнеру Django
kubectl exec -it <django-pod-name> -- /bin/bash

# Подключиться к PostgreSQL
kubectl exec -it <postgres-pod-name> -- psql -U stroymaterials_user -d stroymaterials_db
```

### Проверка здоровья

```bash
# Проверка readiness probe
kubectl get endpoints

# Проверка liveness probe
kubectl describe pod <pod-name>
```

## Остановка и очистка

### Временная остановка

```bash
# Остановить все деплойменты
kubectl scale deployment --all --replicas=0
```

### Полное удаление

```bash
# Удалить все ресурсы
kubectl delete -R -f k8s-manifests/

# Удалить PVC (осторожно! данные будут потеряны)
kubectl delete pvc postgres-pvc
```

### Остановка Minikube

```bash
minikube stop
```

## Продакшен конфигурация

Для продакшена необходимо:

1. **Настроить постоянные хранилища** с правильным StorageClass
2. **Настроить TLS/SSL** для Ingress
3. **Использовать внешние managed сервисы** для БД (RDS, Cloud SQL)
4. **Настроить мониторинг** (Prometheus, Grafana)
5. **Настроить логирование** (ELK Stack, Loki)
6. **Настроить CI/CD** пайплайны
7. **Использовать Secrets Manager** вместо Kubernetes Secrets
8. **Настроить Network Policies** для безопасности
9. **Настроить Resource Quotas** и Limit Ranges
10. **Настроить Horizontal Pod Autoscaler** для автоскейлинга

## Структура файлов

```
k8s-manifests/
├── configmaps/
│   └── app-config.yaml          # Конфигурация приложения
├── secrets/
│   └── app-secrets.yaml         # Секретные данные (пароли, ключи)
├── pvcs/
│   └── postgres-pvc.yaml        # Persistent Volume для БД
├── deployments/
│   ├── postgres-deployment.yaml # Деплоймент PostgreSQL
│   ├── redis-deployment.yaml    # Деплоймент Redis
│   ├── django-deployment.yaml   # Деплоймент Django
│   └── nginx-deployment.yaml    # Деплоймент Nginx
├── services/
│   ├── postgres-service.yaml    # Сервис PostgreSQL
│   ├── redis-service.yaml       # Сервис Redis
│   ├── django-service.yaml      # Сервис Django
│   └── nginx-service.yaml       # Сервис Nginx
├── ingress/
│   └── app-ingress.yaml         # Ingress правила
└── jobs/
    └── import-data-job.yaml     # Job для импорта данных
```

## Следующие шаги

1. Создать Dockerfile для Django приложения
2. Создать Dockerfile для Nginx с конфигурацией
3. Настроить Django settings для работы в Kubernetes
4. Реализовать health check endpoints в Django
5. Настроить сборку образов в CI/CD
6. Протестировать локально на Minikube
