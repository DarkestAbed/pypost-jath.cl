---
title: Data warehousing en Clickhouse en 15 minutos
description: Un breve acercamiento a crear data warehouses en Clickhouse
date: 2021-02-13
slug: data-warehousing-clickhouse
published: true
tags: [clickhouse, data-warehousing]
# categories:
#   - english-spoken
#   - clickhouse
#   - data-warehousing
---

## A primer on building a data store on Clickhouse

I had recently a data engineering challenge: I had to deliver data, wrangled in Spark (personal choice, but since Spark and Databricks are all the hype, why not, right?), into a data warehouse provisioned in Yandex’s own Clickhouse. For those of you who are unaware of it, Clickhouse is an analytical, column-oriented, blazingly fast database, open sourced by their creators. I was, at the moment, unfamiliar with the technology. And if the fun was not enough, I had to dockerize the entire solution, so I had to deal with network communication and APIs. Obviously, I had to write about the problem after I was done coding about it.

Containerizing entire solutions has its own romantic narrative, but on this story I will focus on the coding and experience of using Clickhouse as a data warehousing solution.

---

Clickhouse was initially developed by Yandex, a Russian tech company, to power their web analytics platform. It was then open sourced, and the code can be found on GitHub. It’s also containerized, and the server and client can be both found on their Docker Hub repo. (If you peruse over there, you’ll find a lot of good stuff. Seriously.) It promises between 100 and 1,000x better performance in analytical workloads, and it advertises storage compression and query optimizations, using several database engines, including a remote MySQL engine.

Setting up Clickhouse on a Dockerized environment is as easy as two different commands:

<br>

```bash 
docker run -d \\
    --name some-clickhouse-server \\
    --ulimit nofile=262144:262144 \\
    yandex/clickhouse-server

docker run -it --rm \\
    --link some-clickhouse-server:clickhouse-server \\
        yandex/clickhouse-client \\
        --host clickhouse-server
```

And just like that, you have access to an ephemeral Clickhouse client/server setup! And, thanks to the Docker itself, you needed to install absolutely 0 software on your computed. Except, of course, for Docker.

Great stuff! Innit?

This will get you started with an empty database, a default user, and a set of system tables that are of little use. Good for exploring, but hardly what you want if you need a production (or dev, or QA, or any development-oriented environment) database. To add an initialization SQL script, we must add something to our docker run instruction:

<br>

```bash
docker run -d -v \\
    "$PWD/init.sql:/docker-entrypoint-initdb-d/init.sql" \\
    --name some-clickhouse-server \\
    --ulimit nofile=262144:262144 \\
    yandex/clickhouse-server
```

You’ll see, the Docker image of the Clickhouse server, after starting all necessary services, will look into the /docker-entrypoint-initdb.d folder, and check if there are any SQL or bash scripts to help set up the environment. To have some fun, let’s create a user, a database, and a couple of tables:

<br>

```sql
-- init.sql
DROP DATABASE IF EXISTS database_1;

CREATE DATABASE IF NOT EXISTS database_1;

DROP TABLE IF EXISTS database_1.actividad;

DROP TABLE IF EXISTS database_1.predicciones;

CREATE TABLE IF NOT EXISTS database_1.actividad
(
    clientUUID UUID NOT NULL,
    clientName String,
    clientAddress String,
    clientRegion String,
    clientCountry String,
    clientAge UInt8,
    clientID String,
    clientGroup String,
    activityDate DateTime,
    clientConsumption UInt16,
    activityCode UInt8,
    date_ts String
)
ENGINE = MergeTree()
ORDER BY date_ts
PARTITION BY date_ts
;


CREATE TABLE IF NOT EXISTS database_1.predicciones
(
    clientUUID UUID NOT NULL,
    clientID String,
    clientName String,
    activityDate DateTime,
    date_ts String,
    y Float64,
    yhat Float64
)
ENGINE = MergeTree()
ORDER BY date_ts
PARTITION BY date_ts
;


CREATE USER IF NOT EXISTS usuario_api
    IDENTIFIED WITH plaintext_password 
        BY 'bad_plaintext_password_1'
;

GRANT
    SELECT,
    INSERT,
    ALTER,
    CREATE,
    DROP,
    TRUNCATE
ON database_1.*
TO usuario_api
;
```

A couple of notes on the script we just laid out:

* We’re using the UUID capabilities of Clickhouse to generate a universally unique identifier and store it on the tables we just created.
* Clickhouse has several different table engines available, and we’re using the `MergeTree` engine to support the tables we’re creating. Using this, we need an `ORDER BY` column to act as a `PRIMARY KEY`-esque sorting column.
* We also use a `PARTITION BY` key to maximize the usability and response time of the tables, using the date_ts field as a partitioning (and de facto bucketing) key.
* As a side note, partitioning and bucketing are always good data engineering, since this practice can and will improve performance of your queries. Be mindful of the sorting key always, since too many or too few buckets will increase your CPU I/O overhead.
* We use the `GRANT` statement to allow certain operations to the user we created. This is a powerful operation, and allow us to rely on SQL instead of complex XML files to perform configurations.

Once this is done, we’ll save the file, run the Docker command and log in to our Clickhouse machine to check the new tables and user created:

We see something strange is afoot. We are not seeing our new database nor the new user. And this is due to a configuration issue we must resolve on the `users.xml` file:

We need to create a local copy of the `users.xml` and change the highlighted line as seen on the screenshot. Once we have that ready, we’ll update our Docker command:

<br>

```bash
docker run -d -v \\
    "$PWD/users.xml:/etc/clickhouse-server/users.xml" \\
    -v "$PWD/init.sql:/docker-entrypoint-initdb-d/init.sql" \\
    --name some-clickhouse-server \\
    --ulimit nofile=262144:262144 yandex/clickhouse-server
```

This will override the default user configuration, allowing the Docker image to consume our `init.sql` file and see our changes:

We now can see our database namespace created, and our new user sitting there, ready to be used. Let’s log in using the newly created credentials:

<br>

```bash
docker run -it --rm \\
    --link some-clickhouse-server:clickhouse-server \\
    yandex/clickhouse-client \\
    --host clickhouse-server \\
    --user usuario_api \\
    --password 'bad_plaintext_password_1'
```

Now that everything’s in place, we can do some housekeeping:

* We created a new folder, `db`, to keep the two text files we created, as well as persistent data.
* We will create a `clickhouse.sh` bash script that wil fire up our Docker service, tidying up the startup process.
* We create a `db/data` folder to keep the persistent data that will be stored.

We have what we want now! If you want to look at the source code we created, you can find it on this [GitHub repo](https://github.com/jtapiath-cl/docker_training). On the next article, we will go through the Clickhouse API usage and how to query the data within Clickhouse and using a REST API. Stay tuned!
