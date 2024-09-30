# Goodsale Python Test Task

### Описание:

Нужно написать сервис, который будет:

1.
Открывать [файл с выгрузкой](http://export.admitad.com/ru/webmaster/websites/777011/products/export_adv_products/?user=bloggers_style&code=uzztv9z1ss&feed_id=21908&format=xml)
по маркетплейсу в xml формате и загружать его содержимое (товары, которые заключены в структурах по типу
`<offer id="1779352490"...`) в PostgreSQL таблицу со структурой, описанной ниже
2. Развернуть
   docker-compose [elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)
3. Загрузить все товары в elasticsearch, а затем пройтись про товарам из бд; через elasticsearch найти самые похожие на
   обрабатываемый товар (матчи) (до 5 шт.); и загрузить их uuid в поле similar_sku.

```sql
create table public.sku
(
    uuid                   uuid,
    marketplace_id         integer,
    product_id             bigint,
    title                  text,
    description            text,
    brand                  text,
    seller_id              integer,
    seller_name            text,
    first_image_url        text,
    category_id            integer,
    category_lvl_1         text,
    category_lvl_2         text,
    category_lvl_3         text,
    category_remaining     text,
    features               json,
    rating_count           integer,
    rating_value           double precision,
    price_before_discounts real,
    discount               double precision,
    price_after_discounts  real,
    bonuses                integer,
    sales                  integer,
    inserted_at            timestamp default now(),
    updated_at             timestamp default now(),
    currency               text,
    barcode                bigint,
    similar_sku            uuid[]
);

comment
on column public.sku.uuid is 'id товара в нашей бд';
comment
on column public.sku.marketplace_id is 'id маркетплейса';
comment
on column public.sku.product_id is 'id товара в маркетплейсе';
comment
on column public.sku.title is 'название товара';
comment
on column public.sku.description is 'описание товара';
comment
on column public.sku.category_lvl_1 is 'Первая часть категории товара. Например, для товара, находящегося по пути Детям/Электроника/Детская электроника/Игровая консоль/Игровые консоли и игры/Игровые консоли, в это поле запишется "Детям".';
comment
on column public.sku.category_lvl_2 is 'Вторая часть категории товара. Например, для товара, находящегося по пути Детям/Электроника/Детская электроника/Игровая консоль/Игровые консоли и игры/Игровые консоли, в это поле запишется "Электроника".';
comment
on column public.sku.category_lvl_3 is 'Третья часть категории товара. Например, для товара, находящегося по пути Детям/Электроника/Детская электроника/Игровая консоль/Игровые консоли и игры/Игровые консоли, в это поле запишется "Детская электроника".';
comment
on column public.sku.category_remaining is 'Остаток категории товара. Например, для товара, находящегося по пути Детям/Электроника/Детская электроника/Игровая консоль/Игровые консоли и игры/Игровые консоли, в это поле запишется "Игровая консоль/Игровые консоли и игры/Игровые консоли".';
comment
on column public.sku.features is 'Характеристики товара';
comment
on column public.sku.rating_count is 'Кол-во отзывов о товаре';
comment
on column public.sku.rating_value is 'Рейтинг товара (0-5)';
comment
on column public.sku.barcode is 'Штрихкод';

create index sku_brand_index
    on public.sku (brand);

create unique index sku_marketplace_id_sku_id_uindex
    on public.sku (marketplace_id, product_id);

create unique index sku_uuid_uindex
    on public.sku (uuid);
```

### Проблема:

Файл большой (5+гб), скорее всего полностью в оперативку не влезет, поэтому читать его нужно не полностью сразу, а по
кускам (`lxml.etree.iterparse` в помощь)

### Требования:

- К проекту должен прикладываться файл docker-compose.yml, и сервис должен работать в docker контейнере; elasticsearch
  должен быть описан в этом-же композ файле (ну и, соответственно, запускаться рядом)
- Максимально-возможное кол-во полей, которые есть в файле, должны быть использованы при заполнении таблицы
- Сервис читает файл итеративно, а не весь сразу
- Код следует PEP-8 (везде есть аннотации типов и пр.)

### Дополнительные баллы за:

- Заполнение полей category_lvl_1, category_lvl_2, category_lvl_3, category_remaining данными из файла на основе
  categoryId из оффера и джоина на таблицу категорий в начале файла (подробнее про category_lvl_1 и пр. в коментах к
  полям таблицы в sql выше)
- Запуск postgres из того-же docker-compose файла, что и сервис и авто-создание таблицы при запуске проекта
- файл .pre-commit-config.yaml с линтерами и форматтерами (например - black, flake8, isort). Ну и, соответственно,
  использование их

### Задачи:

- Развернуть у себя docker postgres и создать там таблицу из приложенного SQL скрипта выше
- Написать сервис и провести “матчинг” через elasticsearch
- Залить сервис в github/gitlab и прислать ссылку на проект
- В readme.md файлик добавить 5-10 примеров uuid и similar_sku, которые получились после матчинга (в идеале - сделать
  join их с самими товарами, чтобы было понятно, что на что заматчилось)

---

## Начало работы

Для того чтобы выполнить описанные ниже команды, вам необходимо:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Для разработки

**ПРИМЕЧАНИЕ**: В проекте используется Python 3.12, поэтому сначала необходимо установить его.

Вот краткая инструкция о том, как быстро настроить проект для разработки:

1. Установите [`poetry`](https://python-poetry.org/)
2. Установите зависимости:

```bash
poetry install
poetry shell
```

3. Установите pre-commit hooks: `pre-commit install`

Запустите контейнеры с postgres и elasticsearch: `docker compose up postgres elasticsearch`

4. Примените миграции:

```bash
alembic -c src/models/alembic.ini upgrade head
```

5. Выполните команду в консоле:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Для работы в контейнере

1. Запустите контейнеры: `docker compose up --build`
2. Примените миграции

```sh
alembic -c src/models/alembic.ini upgrade head
```  

---

### Приложение генерирует документацию по API:

http://localhost:8000/docs  
http://localhost:8000/redoc

---

## Пример взаимодействия с приложением

### Получение списка доступных файлов

Если в директории `data` уже есть XML-файлы для обработки, вы можете получить их список с помощью следующего запроса:

```http request
GET http://0.0.0.0:8000/files
Accept: application/json
```

**Пример ответа:**

```json
{
  "files": [
    "test.xml",
    "elektronika_products_20240924_123058.xml"
  ]
}
```

#### Загрузка нового файла

Чтобы загрузить новый XML-файл для обработки, выполните следующий запрос:

```http request
POST http://0.0.0.0:8000/upload
Accept: application/json
Content-Type: multipart/form-data
```

**Пример ответа:**

```json
{
  "filename": "elektronika_products_20240924_123058.xml"
}
```

#### Запуск обработки файла

После того как нужный файл находится в директории `data`, вы можете запустить его обработку:

```http request
POST http://0.0.0.0:8000/process?filename=elektronika_products_20240924_123058.xml
Accept: application/json
```

**Пример ответа:**

```json
{
  "message": "Processing started",
  "job_id": "784e1b32-28af-4f85-89cd-20723765f739"
}
```

#### Проверка статуса обработки

Чтобы узнать текущий статус задачи, используйте следующий запрос, подставив ваш `job_id`:

```http request
GET http://0.0.0.0:8000/progress/{job_id}
Accept: application/json
```

**Пример ответа:**

```json
{
  "job_id": "2dd7095d-4e40-4b37-9865-59d9da9a2d1f",
  "processing_progress": 75.12,
  "update_similar_progress": 0
}
```

**Поля ответа:**

- `processing_progress` — процент завершения загрузки данных в ElasticSearch и базу данных.
- `update_similar_progress` — процент завершения обновления полей `similar_sku`.

#### Получение информации о товаре

После успешной обработки вы можете получить информацию о товаре по его `uuid`:

```http request
GET http://0.0.0.0:8000/sku/{uuid}
Accept: application/json
```

**Пример ответа:**

```json
{
  "uuid": "d121f7de-1188-42c1-b8fe-53db4125f894",
  "product_id": 613876,
  "title": "Штатив Benro T890+MH2N с головой и держателем для смартфона",
  "category_lvl_1": "Все товары",
  "category_lvl_2": "Электроника",
  "category_lvl_3": "Телефоны",
  "category_remaining": "Аксессуары для телефонов/Штативы, держатели и стедикамы",
  "similar_sku": [
    {
      "uuid": "0dda7eb9-1819-46c8-909b-b7beb4e5e7f2",
      "title": "Трипод Benro T560+MH2N, черный"
    },
    {
      "uuid": "2c16f707-a768-49a3-a339-4da8c7429122",
      "title": "Benro MH2N Складной универсальный держатель для смартфона"
    },
    {
      "uuid": "3c5c505e-175c-47ad-a276-9b8513da293f",
      "title": "Benro MH2N Складной универсальный держатель для смартфона"
    },
    {
      "uuid": "b4a56f78-0912-4d86-b7b7-71173f0813ed",
      "title": "Штатив Benro T890+MH2N с головой и держателем для смартфона"
    },
    {
      "uuid": "d121f7de-1188-42c1-b8fe-53db4125f894",
      "title": "Штатив Benro T890+MH2N с головой и держателем для смартфона"
    }
  ]
}
```

---

## Примеры обработки
```JSON
{
  "uuid": "f36fc3f5-c28f-47c9-b264-3dbb6a9e6348",
  "product_id": 9279079,
  "title": "Фотоаппарат Nikon D7100 Body, черный",
  "category_lvl_1": "Все товары",
  "category_lvl_2": "Электроника",
  "category_lvl_3": "Фото и видеокамеры",
  "category_remaining": "Фотоаппараты",
  "similar_sku": [
    {
      "uuid": "6ad655cb-722a-4e17-853d-feb30470e748",
      "title": "Фотоаппарат Nikon D5100 Body, черный"
    },
    {
      "uuid": "8402516a-e826-4a09-adad-51c8b038697b",
      "title": "Объектив Nikon 50mm f/1.4D AF Nikkor, черный"
    },
    {
      "uuid": "9a9da73c-0a5e-4d61-b921-752452e772f7",
      "title": "Фотоаппарат Nikon D5200 Body, черный"
    },
    {
      "uuid": "f28cb311-21a2-48b8-8ed6-55710719366d",
      "title": "Фотоаппарат Nikon D5200 Body, черный"
    },
    {
      "uuid": "f36fc3f5-c28f-47c9-b264-3dbb6a9e6348",
      "title": "Фотоаппарат Nikon D7100 Body, черный"
    }
  ]
}
```

```JSON
{
  "uuid": "f9f2fde2-fc69-402b-a6e6-39fa2d8c4478",
  "product_id": 808926,
  "title": "Диктофон с аккумулятором Эдик-mini DIME mod: B-120 (O43731MI) + подарок (Повербанк 10000 mAh) - диктофоны с датчиком, диктофон записать голос / дикт",
  "category_lvl_1": "Все товары",
  "category_lvl_2": "Электроника",
  "category_lvl_3": "Портативная техника",
  "category_remaining": "Диктофоны",
  "similar_sku": [
    {
      "uuid": "604c6d52-8589-47b0-b91b-0aa70f9ae579",
      "title": "Диктофон с распознаванием речи Edic-mini TINY+ мод: A81-150HQ подарок (повербанк 10000 mAh) мини диктофон / цифровой диктофон - по голосу (VAS)"
    },
    {
      "uuid": "8a90d111-c714-4432-853a-7d777c3a6f29",
      "title": "Мини диктофон Эдик-mini Micro-SD mod: A-23 (W18968CI) + 2 подарка (Power-bank 10000 mAh + SD карта)"
    },
    {
      "uuid": "eed5083d-56f9-43aa-9260-67b8daabbd45",
      "title": "Диктофон с аккумулятором Эдик-mini DIME mod: B-120 (O43731MI) + подарок (Повербанк 10000 mAh) - диктофоны с датчиком, диктофон записать голос / дикт"
    },
    {
      "uuid": "f3b23fa6-5614-44e9-9d82-d84d626c8b60",
      "title": "Диктофон с распознаванием речи Edic-mini TINY+ мод: A81-150HQ подарок (повербанк 10000 mAh) мини диктофон / цифровой диктофон - по голосу (VAS)"
    },
    {
      "uuid": "f9f2fde2-fc69-402b-a6e6-39fa2d8c4478",
      "title": "Диктофон с аккумулятором Эдик-mini DIME mod: B-120 (O43731MI) + подарок (Повербанк 10000 mAh) - диктофоны с датчиком, диктофон записать голос / дикт"
    }
  ]
}
```

```JSON
{
  "uuid": "6bb3586d-1951-4e7b-a393-6db1d2dca567",
  "product_id": 3870175,
  "title": "Телефон Panasonic KX-TS2352 черный",
  "category_lvl_1": "Все товары",
  "category_lvl_2": "Электроника",
  "category_lvl_3": "Телефоны",
  "category_remaining": "Проводные телефоны",
  "similar_sku": [
    {
      "uuid": "00d5de00-0211-403e-bae0-4f701998911a",
      "title": "Телефон Panasonic KX-TS2382 черный"
    },
    {
      "uuid": "6bb3586d-1951-4e7b-a393-6db1d2dca567",
      "title": "Телефон Panasonic KX-TS2352 черный"
    },
    {
      "uuid": "a5ba257b-2533-41d7-a4b6-dff6779bce8f",
      "title": "Телефон Panasonic KX-TS2352 черный"
    },
    {
      "uuid": "b0317d90-bf1a-497e-816a-d01119245471",
      "title": "Телефон Panasonic KX-TS2382 черный"
    },
    {
      "uuid": "c7ca6666-d597-44f7-acb1-2c1cb48db3a3",
      "title": "Телефон Panasonic KX-TS2352 белый"
    }
  ]
}
```

```JSON
{
  "uuid": "ec33f7cc-ede2-46dd-9830-4d95d0c4706c",
  "product_id": 5049557,
  "title": "Проводные наушники SVEN AP-540, черный",
  "category_lvl_1": "Все товары",
  "category_lvl_2": "Электроника",
  "category_lvl_3": "Портативная техника",
  "category_remaining": "Наушники и гарнитуры",
  "similar_sku": [
    {
      "uuid": "1e865daa-8252-4668-a052-d575978a1f0b",
      "title": "Проводные наушники SVEN AP-G888MV, черный, красный"
    },
    {
      "uuid": "5240372b-4545-4009-b7ae-d5823339e0a2",
      "title": "Проводные наушники SVEN AP-670MV, черный"
    },
    {
      "uuid": "a7a7e28e-25b7-48e9-b754-e873cb1927fb",
      "title": "Проводные наушники SVEN AP-675MV, черный"
    },
    {
      "uuid": "ec33f7cc-ede2-46dd-9830-4d95d0c4706c",
      "title": "Проводные наушники SVEN AP-540, черный"
    },
    {
      "uuid": "fcf292a8-22b6-4b6f-b01d-610df60b3ca5",
      "title": "Проводные наушники SVEN AP-940MV, черный/красный"
    }
  ]
}
```

```JSON
{
  "uuid": "9205fd03-4fde-450e-a5ae-e529486924b0",
  "product_id": 5622424,
  "title": "Очки виртуальной реальности RITMIX RVR-600",
  "category_lvl_1": "Все товары",
  "category_lvl_2": "Электроника",
  "category_lvl_3": "Портативная техника",
  "category_remaining": "VR-очки",
  "similar_sku": [
    {
      "uuid": "16ce01d0-db74-40b7-85c4-38b4691f8f14",
      "title": "Ritmix RVR-400, черный"
    },
    {
      "uuid": "5d6cf2f7-8fbd-4c10-8180-dc1bcb4230d1",
      "title": "Очки виртуальной реальности RITMIX RVR-600"
    },
    {
      "uuid": "9205fd03-4fde-450e-a5ae-e529486924b0",
      "title": "Очки виртуальной реальности RITMIX RVR-600"
    },
    {
      "uuid": "d10a0e86-8c97-4e03-95fe-103a6a19c221",
      "title": "Очки виртуальной реальности RITMIX RVR-200, телефоны шириной до 8см, регулировка линз, чёрные"
    },
    {
      "uuid": "d23c939a-b251-4361-8a2d-2be79c858d12",
      "title": "Очки виртуальной реальности RITMIX RVR-200, телефоны шириной до 8см, регулировка линз, чёрные"
    }
  ]
}
```
