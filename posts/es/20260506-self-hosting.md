---
title: "Self hosting"
date: 2026-05-06
# author: jath
published: true
slug: self-hosting
description: "Post introductiorio a la muy probable serie de posts respecto de la autogestion de software en un laboratorio local. Porque el camino del self-hosting es un camino largo y muy interesante!"
tags: [self-hosted, home-lab]
  # - selfhosted
  # - home-lab
toc: true
---

Hace unos meses empece el camino del _self-hosting_, porque queria dejar de depender de algunos servicios que usaba y pagaba en mi vida. Servicios como streaming, libros en linea, IDE descentralizado y algunos mas. Y, como muchos entusiastas del DIY saben, entre en un agujero de conejo.

Si bien voy a escribir mas del mundo del self-host, no quiero comenzar con un larguisimo recuento de todo lo que he hecho. Creo que es bueno empezar con las lecciones aprendidas hasta este momento.

## Poder hostear no significa que _debas_ hostear

El camino del self-hosting es tan largo como uno quiera. Y en algun punto, y pareciera que no soy el unico, el camino uno lo va alargando solo _porque si_. Por ejemplo: si no tienes muchos proyectos que trackear, y no necesitas gestionar tu tiempo y enviar boletas por horas trabajadas, no hay razon para tener algo como [Kimai](https://www.kimai.org/en/); si no lees, para que querrias [Kavita](http://www.kavitareader.com/) o [Calibre Web](https://github.com/janeczku/calibre-web)?

Pero ahi esta uno, probando cuanta herramienta aparece. Gestion de proyectos? Vamos. Audiolibros y podcasts? Claro que si. Gestion documental y escaneo de boletas para flujos automaticos de invoicing, a clientes que no tienes? Voy de encefalo!

Una de las primeras lecciones que aprendi en el mundo de la autogestion, es que _porque puedo_ no es una respuesta suficiente. Tu stack tecnologico DEBE tener sustento en tu forma de trabajar y objetivos.

## Es vital tener servicios que manejen los contenedores, y es mas vital tener respaldos de los contenedores que sirves

Docker y Docker Compose, e incluso Kubernetes, si nos vamos en esa, son servicios tremendente poderosos, y han llegado a un punto de experiencia de uso donde puede ser hasta _comodo_ el desplegar varios stacks en paralelo. Hell, es parte de [lo que enseño]()https://www.duoc.cl/carreras/ingenieria-en-desarrollo-de-software-2/.

Pero por muy comodo que sea hacer `docker compose up --build`, pocas cosas superan la experiencia de una experiencia visual. Por eso una de las mejores adiciones que hice a mi stack fue [Portainer](https://www.portainer.io/): una herramienta que gestiona mis stacks en multiples nodos. De hecho, me permite conectar varios servidores y gestionar todo en un solo punto central.

Que es lo mismo que decir "un punto central de fallo". Porque, cuando ese servidor crasheo, y tuve que regenerar los stacks, no tenia respaldados los comandos de Docker Compose. Y no hay una forma facil de rehacerlo, sobre todo cuando tienes variables de entorno en juego. Asi que si, es importante centralizar las gestiones, y es mas importante mantener un registro de lo que uno hace. Un registro _respaldado_.

## No me canso de decirlo: **respaldos, respaldos, respaldos**

De hecho, no conozco ningun tecnologista que diga algo distinto: _respaldos, respaldos, respaldos_. Porque el fallo de una pieza no es una cuestion de oportunidad, sino de tiempo: no es _si es que_ va a fallar, es _cuando es que_ va a fallar. Y cuando las cosas fallan, y no tienes forma de volver en el tiempo, pues toca el proceso doloroso de **recrear todo a mano**.

Lo que no solo es una ladilla. Es 100% evitable.

## Encuentra tus servicios vitales y mantenlos siempre vivos

Creo que parte de las razones por las cuales, cuando entras en el mundo de la autogestion, pruebas tantos servicios, es que hay muchas cosas que suenan cool (como [Coolify](https://coolify.io/) o [Appwrite](https://appwrite.io/docs/advanced/self-hosting), por mencionar dos que tengo en la punta de la lengua) y que pareciera que resuelven problemas que uno podria llegar a tener. Como, por ejemplo, Appwrite.

[Appwrite](https://appwrite.io/) es un servicio que permite desplegar otros microservicios, como bases de datos y backends, de manera rapida y mas efectiva: incluye cosas parecidas a pipelines de CI/CD, wrappers comodos para frameworks comunes (Bun, Node, React, etc), y se puede integrar en el flujo de desarrollo de manera muy sencilla. Suena a un servicio de ensueño, cierto? Y estoy profundamente seguro que, para alguna gente, lo es.

Pero si uno no desarrolla aplicaciones, y no pretende alojarlas en una red privada, por que te tomarias la molestia de instalar y configurar y desplegar algo asi? Porque es un problema que _podrias llegar a tener_?

Un par de años en el mundo de la autogestion de software me han enseñado que lo mas importante no es resolver problemas eventuales, potenciales, que viven en el "quizas"; lo fundamental es obtener y desplegar herramientas que te permitan mejorar tu flujo de trabajo **actual**, porque los problemas del despues no se pueden solucionar en el ahora, pero los problemas del ahora que quedan sin solucion, te joden en el despues. Por eso una de mis lecciones aprendidas, y de mis recomendaciones, es probar cosas que te apoyen ahora, y luego puedes ir agregando mas.

Y dicho esto, la disponibilidad es un tema tremendamente relevante. Como historia de precaucion: mi calendario y mis contactos existen en un servidor con [Radicale](https://radicale.org/v3.html), en una maquina que es susceptible a reinicios. Y me ha pasado que, sin previo aviso, el server se cae. Y me quedo sin poder sincronizar mis calendarios entre mis dispositivos. Entonces, dos lecciones:

- Mi servidor de CalDAV debe estar configurado para tener la maxima disponibilidad posible
- Necesito un servicio que monitoree y me alerte cuando un servicio (o peor, un servidor completo) no esta disponible

Asi llegue a [Beszel](https://beszel.dev/), un excelente servicio de monitoreo y alertas tempranas de infraestructura. En algun momento voy a escribir mas de el; por ahora basta decir que no puedo tener un laboratorio sin este servicio disponible y configurado.

## Si no hay un servicio que cumpla tus expectativas, puedes construirlo tu mismo/a/e

Y, para terminar, les puedo ASEGURAR que en algun momento van a tener una necesidad que nadie en el mercado ha pensado en suplir. Incluso en el mundo del codigo abierto. Cuando ese momento llegue, y sobre todo si tienen soltura y las capacidades para programar y desplegar software, _**construyelo tu mismo/a/e**_. Construyelo, desarrollalo, y ponlo en linea. El mundo siempre va a ser un mejor lugar despues de que aportes ese pequeño granito de arena.

Si tu tambien eres un entusiasta de la autogestion, o si estas pensando en entrar a este mundo, [escribeme! Conversemos!](mailto:javier@jath.cl)
