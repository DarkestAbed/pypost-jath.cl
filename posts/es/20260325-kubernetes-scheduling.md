---
title: "Cómo Kubernetes decide dónde ejecutar un Pod"
description: "Un recorrido por el pipeline del kube-scheduler: predicados, prioridades, y por qué tu Pod terminó en ese nodo."
date: 2026-03-15
# author: jath
slug: kubernetes-scheduling
published: true
tags: [kubernetes, infraestructura, devops]
  # - kubernetes
  # - infraestructura
  # - devops
series: "kubernetes-internals"
series_part: 1
toc: true
---

Cuando ejecutas `kubectl apply -f pod.yaml`, el Pod aparece en algún nodo del clúster. Parece magia. No lo es. Hay un proceso determinista detrás, y entenderlo te permite predecir —y controlar— dónde aterrizan tus cargas de trabajo.

## El _kube-scheduler_

El `kube-scheduler` es un proceso independiente del control plane. Su única responsabilidad es asignar Pods a nodos. No los ejecuta, no los monitorea: solo decide el `spec.nodeName`.

El loop principal es simple en concepto:

```text
1. Observa la cola de Pods sin nodo asignado
2. Para cada Pod, filtra los nodos que NO pueden ejecutarlo
3. Entre los nodos restantes, puntúa y elige el mejor
4. Escribe spec.nodeName en el Pod
```

Cada paso tiene complejidad real. Vamos por partes.

## Fase 1: Filtering (predicados)

El scheduler aplica una serie de **plugins de filtrado** que eliminan nodos incompatibles. Los más importantes:

### NodeResourcesFit

Verifica que el nodo tenga suficientes recursos para los `requests` del Pod:

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "256Mi"
```

Si el nodo tiene 300m de CPU disponible, queda eliminado. Los `requests` son la unidad de planificación — los `limits` no influyen en el scheduling.

### NodeSelector y NodeAffinity

```yaml
nodeSelector:
  kubernetes.io/arch: amd64
```

Elimina nodos que no tengan esa etiqueta. `nodeAffinity` ofrece la misma funcionalidad con sintaxis más expresiva: `requiredDuringSchedulingIgnoredDuringExecution` es un requisito duro (equivalente a `nodeSelector`), `preferredDuringScheduling...` es una preferencia que influye en la puntuación.

### TaintToleration

Un nodo con `taint` rechaza Pods que no tengan la `toleration` correspondiente. Útil para nodos GPU, nodos de sistema, o cualquier nodo que deba reservarse:

```bash
kubectl taint nodes gpu-node-1 dedicated=gpu:NoSchedule
```

Solo Pods con esta toleration pueden ser programados ahí:

```yaml
tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "gpu"
    effect: "NoSchedule"
```

### PodTopologySpread

Garantiza distribución entre zonas de disponibilidad o nodos. Evita que todos tus Pods terminen en el mismo nodo físico:

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: mi-servicio
```

`maxSkew: 1` significa que la diferencia entre el nodo con más Pods y el nodo con menos no puede ser mayor a 1.

## Fase 2: Scoring (prioridades)

De los nodos que sobrevivieron el filtrado, el scheduler asigna una puntuación de 0 a 100 a cada uno. Los plugins de scoring más relevantes:

| Plugin | Qué favorece |
|--------|-------------|
| `LeastAllocated` | Nodos con más recursos libres (spreading) |
| `MostAllocated` | Nodos más llenos (bin-packing) |
| `NodeAffinity` | Nodos que coinciden con preferencias soft |
| `InterPodAffinity` | Co-localización con otros Pods |
| `ImageLocality` | Nodos que ya tienen la imagen descargada |

Por defecto, `LeastAllocated` tiene el mayor peso. El resultado es que los Pods se distribuyen entre nodos.

## Fase 3: Selección y binding

El scheduler elige el nodo con mayor puntuación. En caso de empate, elige al azar entre los empatados.

Luego ejecuta el **binding**: una escritura en la API de Kubernetes que actualiza `spec.nodeName` del Pod. El `kubelet` del nodo destino detecta el cambio y arranca los contenedores.

## Preemption: cuando no hay espacio

Si ningún nodo pasa el filtrado, el Pod queda en estado `Pending`. El scheduler puede entonces intentar **preempción**: buscar Pods de menor prioridad en algún nodo, eliminarlos, y liberar espacio para el Pod pendiente.

Esto requiere que el Pod tenga una `PriorityClass` definida:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
```

```yaml
spec:
  priorityClassName: high-priority
```

Un Pod con `value: 1000000` puede desalojar Pods con valores menores. Los Pods sin `priorityClassName` tienen prioridad 0.

## Diagnóstico práctico

Si un Pod está en `Pending`, el primer lugar donde mirar:

```bash
kubectl describe pod <nombre>
```

La sección `Events` dice exactamente qué plugin falló y por qué:

```
Warning  FailedScheduling  0/3 nodes are available:
  1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: },
  2 node(s) didn't match Pod's node affinity/selector.
```

También existe el **scheduler extender** y el framework de plugins para personalización avanzada, pero eso es material para otro artículo.

## Resumen

El kube-scheduler toma una decisión en dos fases: primero elimina los nodos que no pueden ejecutar el Pod (filtering), luego elige el mejor entre los restantes (scoring). La preempción existe como mecanismo de último recurso para Pods de alta prioridad.

Entender estas fases te permite depurar Pods en `Pending`, diseñar topologías de nodos con intención, y escribir manifiestos que expresen exactamente dónde debe correr tu carga de trabajo.
