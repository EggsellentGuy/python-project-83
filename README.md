# Page Analyzer

[![Actions Status](https://github.com/EggsellentGuy/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/EggsellentGuy/python-project-83/actions)
[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-dark.svg)](https://sonarcloud.io/summary/new_code?id=EggsellentGuy_python-project-83)


**Page Analyzer** — веб-приложение на Flask для анализа веб-страниц на SEO-пригодность.  


Приложение позволяет:
- добавлять сайты для анализа;
- выполнять HTTP-проверку страниц;
- получать SEO-показатели (status code, h1, title, description);
- сохранять результаты проверок в базу данных.


### Можно попробовать онлайн

Приложение задеплоено на Render:  
    https://python-project-83-yyqq.onrender.com





### Установка и запуск

### 1) Клонирование репозитория

```bash
git clone https://github.com/EggsellentGuy/python-project-83.git
cd python-project-83
```
### 2) Установка зависимостей
```bash
make install
```
### 3) Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/page_analyzer
SECRET_KEY=your-secret-key
```
### 4) Создание базы данных
```bash
psql -d page_analyzer -f database.sql
```

### 5) Запуск приложения
```bash
make dev
```

Приложение будет доступно по адресу:
`http://localhost:8000`