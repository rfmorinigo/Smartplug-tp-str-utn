# Enchufe Inteligente IoT – Grupo 10

**Materia:** Sistemas de Tiempo Real  
**Comisión:** S32  
**Docente:** Mazzeo, Hugo  

**Integrantes:**

- Llontop, Alejandro – Legajo N° 31890  
- Morinigo, Roger – Legajo N° 23920  
- Ross, Nicolás – Legajo N° 32640  

---

## Índice

1. Introducción  
   1.1 Razones que impulsaron el trabajo  
   1.2 Objetivos del trabajo  

2. Marco teórico  
   2.1 Enchufes inteligentes y domótica  
   2.2 Consumo eléctrico, potencia y energía  
   2.3 Protocolo MQTT y broker Mosquitto  

3. Propuesta de trabajo  
   3.1 Definición del problema  
   3.2 Alcance del proyecto  

4. Especificación del sistema desarrollado  
   4.1 Componentes hardware simulados en Wokwi  
   4.2 Broker MQTT utilizado  
   4.3 Interfaz gráfica de usuario en Python  

5. Arquitectura y funcionamiento  
   5.1 Diagrama de bloques del sistema  
   5.2 Tópicos MQTT y flujo de datos  
   5.3 Lógica del ESP32 (medición y protección)  
   5.4 Lógica de la GUI (control y monitoreo)  

6. Simulación y pruebas  
   6.1 Escenario de simulación en Wokwi  
   6.2 Casos de prueba  

7. Posible integración con Node-RED y Telegram  

8. Limitaciones y trabajo futuro  

9. Conclusiones  

10. Referencias  

---

## 1. Introducción

### 1.1 Razones que impulsaron el trabajo

El crecimiento de la domótica y del Internet de las Cosas (IoT) ha impulsado la aparición de dispositivos que permiten automatizar tareas cotidianas en el hogar. En particular, los enchufes inteligentes (smart plugs) ofrecen una forma sencilla de convertir dispositivos eléctricos convencionales en elementos controlables y monitoreables de manera remota, sin necesidad de reemplazarlos por equipos nuevos.

Al momento de definir el trabajo práctico de la materia Sistemas de Tiempo Real, el grupo buscó una idea que pudiera trasladarse a un escenario real, que permitiera medir magnitudes eléctricas, aplicar lógica de control y, al mismo tiempo, integrar comunicaciones de red para el monitoreo remoto. El enchufe inteligente IoT cumple con estos objetivos y permite trabajar con conceptos centrales de la asignatura.

### 1.2 Objetivos del trabajo

Los objetivos principales del proyecto son:

- Diseñar e implementar un prototipo de enchufe inteligente capaz de medir una señal analógica equivalente a corriente de carga, calcular la potencia consumida y publicar estos datos en tiempo real mediante MQTT.
- Permitir el control remoto del enchufe (encendido/apagado) desde un cliente externo conectado al mismo broker MQTT.
- Incorporar un mecanismo de protección por sobrecarga que detecte corrientes superiores a un umbral preestablecido y corte automáticamente la salida.
- Desarrollar una interfaz gráfica de escritorio que permita al usuario controlar el enchufe, visualizar la potencia instantánea, integrar la energía consumida (kWh), estimar el costo económico y registrar eventos relevantes en un log.

---

## 2. Marco teórico

### 2.1 Enchufes inteligentes y domótica

Un enchufe inteligente es un dispositivo que se intercala entre la toma de corriente de la red domiciliaria y la carga (por ejemplo, una lámpara, una cafetera o un cargador). Este dispositivo permite encender y apagar la alimentación de forma remota, medir variables eléctricas como corriente y potencia, y, en sistemas comerciales, integrarse con plataformas de hogar conectado.

En el presente proyecto se trabaja con un prototipo orientado a la simulación, pero con una arquitectura trasladable a un diseño físico real. El énfasis está puesto en la lógica de control, la protección por sobrecarga y la integración mediante MQTT.

### 2.2 Consumo eléctrico, potencia y energía

La potencia activa consumida por una carga resistiva puede aproximarse como:

> P = V × I

donde **V** es la tensión de línea (en este caso se asume 220 V constantes en la simulación) e **I** es la corriente consumida por la carga (simulada mediante un potenciómetro).

La energía consumida se obtiene integrando la potencia en el tiempo. En forma discreta, se puede aproximar mediante:

> E [Wh] ≈ Σ (P × Δt / 3600)

La interfaz gráfica acumula energía en Wh, la convierte a kWh y utiliza este valor para estimar el costo económico según un valor de referencia de tarifa eléctrica.

### 2.3 Protocolo MQTT y broker Mosquitto

MQTT (Message Queuing Telemetry Transport) es un protocolo de mensajería ligero basado en un modelo publicador/suscriptor. Es ampliamente utilizado en aplicaciones IoT debido a su bajo overhead y simplicidad. En este modelo, los dispositivos publican mensajes en tópicos específicos, mientras que otros dispositivos se suscriben a esos tópicos para recibir los datos.

En este proyecto se utiliza el broker público `test.mosquitto.org`, provisto por Eclipse Mosquitto. Tanto el ESP32 simulado en Wokwi como la interfaz gráfica en Python se conectan a este broker para intercambiar los mensajes necesarios para el control y monitoreo del enchufe inteligente.

---

## 3. Propuesta de trabajo

### 3.1 Definición del problema

El problema abordado consiste en implementar un sistema de monitoreo y control inteligente sobre un aparato eléctrico conectado a un enchufe smart. Se busca medir y reportar la potencia consumida, permitir el control remoto de la alimentación y proteger al sistema frente a sobrecargas, cortando automáticamente el suministro cuando se supera un umbral de seguridad configurable.

### 3.2 Alcance del proyecto

El alcance del proyecto incluye la implementación de un prototipo funcional en entorno de simulación, utilizando un ESP32 DevKit en Wokwi, un broker MQTT público y una interfaz gráfica de escritorio en Python. No se trabaja con tensión de red real ni con cargas físicas; la corriente se simula mediante señales analógicas. El diseño, sin embargo, es trasladable a un prototipo físico incorporando los elementos de aislación y seguridad eléctrica correspondientes.

---

## 4. Especificación del sistema desarrollado

### 4.1 Componentes hardware simulados en Wokwi

En el simulador Wokwi se modelan los siguientes componentes principales:

- **ESP32 DevKit (ESP32 Dev Module):** microcontrolador con conectividad WiFi integrada, encargado de ejecutar el firmware, conectarse al broker MQTT, leer las entradas analógicas, controlar el relé y manejar la interfaz local (LCD y LED RGB).
- **Módulo de relé:** representa el elemento de conmutación que, en un diseño físico, permitiría cortar o restablecer la alimentación de la carga conectada al enchufe.
- **Potenciómetros (2 unidades):** uno de ellos se utiliza para simular la corriente de carga, aportando una señal analógica que el ESP32 interpreta como un valor de corriente en amperios. El segundo potenciómetro se reserva para simulaciones de tensión, aunque en la versión actual se asume un valor fijo de 220 V.
- **Pantalla LCD I2C 20x4:** proporciona una interfaz local donde se visualizan la corriente, la tensión, la potencia y mensajes de estado, incluyendo indicaciones de sobrecarga y desconexión.
- **LED RGB de cátodo común:** actúa como indicador visual de estado de carga, cambiando de color según el nivel de corriente detectado (baja, normal o elevada).

### 4.2 Broker MQTT utilizado

El broker utilizado es el servidor público `test.mosquitto.org`, basado en Eclipse Mosquitto. El ESP32 y la aplicación Python se conectan a este broker a través del puerto 1883, utilizando tópicos específicos para el control del relé, la publicación de la potencia y la configuración del umbral de sobrecarga.

### 4.3 Interfaz gráfica de usuario en Python

La interfaz gráfica se implementa en Python utilizando Tkinter para la construcción de la ventana, botones y etiquetas, y la librería `paho-mqtt` como cliente MQTT. La GUI permite encender y apagar el enchufe, visualizar la potencia instantánea, configurar el umbral de sobrecarga en Watts, acumular energía consumida en kWh, estimar el costo económico y mantener un log de eventos relevantes.

---

## 5. Arquitectura y funcionamiento

### 5.1 Diagrama de bloques del sistema

Desde una perspectiva de alto nivel, el sistema puede describirse mediante los siguientes bloques:

- **Módulo de medición y control (ESP32):** adquiere la señal analógica del potenciómetro, calcula corriente y potencia, aplica la lógica de protección por sobrecarga y controla el relé, la LCD y el LED RGB.
- **Broker MQTT:** actúa como intermediario entre el ESP32 y la interfaz gráfica, recibiendo y distribuyendo los mensajes publicados en los distintos tópicos.
- **Interfaz gráfica en Python:** permite al usuario final interactuar con el sistema, enviando comandos al enchufe y recibiendo en tiempo real las mediciones de potencia y el estado del sistema.

### 5.2 Tópicos MQTT y flujo de datos

Se definieron los siguientes tópicos MQTT principales:

- `Smart_Plug-Relay`: la GUI publica `"1"` para encender el enchufe y `"0"` para apagarlo. El ESP32 está suscrito a este tópico.
- `Power`: el ESP32 publica periódicamente la potencia instantánea medida (en Watts). La GUI se suscribe a este tópico para actualizar la visualización y calcular energía y costos.
- `Smart_Plug/Overload_W`: la GUI publica un valor numérico en Watts correspondiente al umbral de sobrecarga deseado. El ESP32 recibe este valor, lo convierte internamente a corriente (Amperios) y actualiza la variable `CURRENT_LIMIT`, que se utiliza para la protección por sobrecarga.

### 5.3 Lógica del ESP32 (medición y protección)

El firmware del ESP32 se encarga de la conexión WiFi, la conexión al broker MQTT y la lógica de medición y control. En cada ciclo de ejecución, cuando el relé está en estado activo, el microcontrolador lee la entrada analógica asociada al potenciómetro de corriente, la convierte a un valor de corriente entre 0 y 5 A, asume una tensión fija de 220 V y calcula la potencia instantánea. Estos valores se muestran en la pantalla LCD y el color del LED RGB se actualiza según el nivel de corriente.

El mismo bucle envía la potencia calculada al broker MQTT mediante el tópico `Power`. Por otro lado, el callback de MQTT procesa los comandos de encendido/apagado recibidos en `Smart_Plug-Relay` y, adicionalmente, la configuración del umbral de sobrecarga recibida en `Smart_Plug/Overload_W`. A partir de este umbral, el firmware compara la corriente medida con `CURRENT_LIMIT` y, si se supera, muestra un mensaje de sobrecarga, hace parpadear el LED RGB en rojo y abre el relé para cortar la alimentación.

### 5.4 Lógica de la GUI (control y monitoreo)

La interfaz gráfica, desarrollada en Python, se conecta al mismo broker MQTT y se suscribe al tópico `Power` para recibir los valores de potencia instantánea. A partir de estos datos, actualiza la etiqueta de potencia, integra la energía consumida en el tiempo y calcula un costo estimado en función de un costo por kWh configurable en el código.

La GUI incluye controles para enviar órdenes de encendido y apagado al enchufe mediante el tópico `Smart_Plug-Relay` y permite configurar, a través de un campo de entrada, el umbral de sobrecarga en Watts. Este umbral se almacena en la aplicación y, además, se envía al ESP32 publicando en `Smart_Plug/Overload_W`, de forma que el criterio de sobrecarga sea coherente en ambos extremos.

La aplicación mantiene un log de eventos donde se registran las acciones del usuario (encendidos, apagados, cambios de umbral), los apagados automáticos por sobrecarga y los problemas de comunicación detectados. Asimismo, implementa un mecanismo de supervisión que detecta la ausencia prolongada de mensajes en el tópico `Power` y notifica al usuario de una posible pérdida de comunicación con el equipo IoT.

---

## 6. Simulación y pruebas

### 6.1 Escenario de simulación en Wokwi

La simulación se llevó a cabo en la plataforma Wokwi, utilizando un proyecto que integra el ESP32 DevKit, los potenciómetros, el módulo de relé, la pantalla LCD I2C y el LED RGB. El simulador permite variar manualmente las posiciones de los potenciómetros para emular distintos escenarios de carga y observar en tiempo real el comportamiento del firmware.

Mientras el ESP32 ejecuta el código en Wokwi y publica los datos de potencia a través del broker `test.mosquitto.org`, la interfaz gráfica en Python se conecta desde una PC con Windows y muestra las mediciones, permite el control del relé y registra eventos.

### 6.2 Casos de prueba

Se realizaron, entre otras, las siguientes pruebas:

- Encendido y apagado manual del enchufe desde la GUI, verificando que el estado del relé y los mensajes en el LCD coincidan con las órdenes enviadas.
- Variación del potenciómetro de corriente para emular distintos niveles de carga, comprobando la actualización de la potencia en la GUI y el cambio de color del LED RGB según la corriente.
- Configuración de distintos valores de umbral de sobrecarga en la GUI y verificación de que, al superarlos, el ESP32 corta el relé, muestra el mensaje de sobrecarga y la GUI registra el evento correspondiente.
- Interrupción de la simulación del ESP32 en Wokwi para observar el comportamiento de la interfaz gráfica frente a la ausencia de datos, verificando la detección de pérdida de comunicación y el registro del evento en el log.

---

## 7. Posible integración con Node-RED y Telegram

Si bien la versión actual del sistema no integra Node-RED en la cadena de ejecución, se considera esta herramienta como una opción natural para ampliar la funcionalidad del prototipo. Node-RED es una plataforma de programación por flujo que permite conectar fácilmente dispositivos IoT, servicios web y sistemas de mensajería.

En particular, un flujo típico consistiría en suscribirse desde Node-RED al tópico `Power` del broker MQTT, analizar la potencia recibida mediante nodos de función y de comparación y, cuando se detectan condiciones de sobrecarga, generar acciones adicionales tales como el envío de notificaciones a un bot de Telegram o el almacenamiento de los datos en una base de datos para análisis histórico. Esta integración se deja planteada como trabajo futuro y no se encuentra aún implementada en la versión presentada.

---

## 8. Limitaciones y trabajo futuro

Entre las principales limitaciones del sistema desarrollado se destacan las siguientes:

- El proyecto se ejecuta íntegramente en entorno de simulación; no se trabaja con tensión de red ni con cargas físicas, por lo que no se abordan aspectos de seguridad eléctrica y aislación.
- La medición de corriente se basa en un potenciómetro y no en un sensor real, por lo que no se consideran factores como el factor de potencia o posibles formas de onda no senoidales.
- La estimación de costos se realiza utilizando un valor de referencia de tarifa eléctrica, que debería ajustarse según la distribuidora y el segmento tarifario de cada usuario.

Como líneas de trabajo futuro se proponen las siguientes mejoras:

- Implementar un prototipo físico incorporando sensores de corriente (por ejemplo, ACS712) y un módulo de relé adecuado para maniobrar cargas reales de 220 V, respetando las normas de seguridad eléctrica.
- Integrar Node-RED como capa de orquestación IoT para almacenar históricos de consumo, generar dashboards y enviar notificaciones a servicios externos (por ejemplo, Telegram) ante eventos de sobrecarga.
- Agregar almacenamiento local o remoto de registros de energía y eventos para permitir análisis más detallados del comportamiento de las cargas en el tiempo.

---

## 9. Conclusiones

El proyecto desarrollado demuestra la implementación de un enchufe inteligente IoT que combina control y protección local en un microcontrolador ESP32 con monitoreo y configuración remota a través de MQTT y una interfaz gráfica de escritorio en Python. Aunque se encuentra en un entorno de simulación, la arquitectura propuesta resulta representativa de un sistema real de domótica, en el que un usuario puede tanto controlar la alimentación de una carga como conocer su consumo energético y recibir alertas ante situaciones de sobrecarga.

Desde la perspectiva de la materia Sistemas de Tiempo Real, el trabajo integra conceptos de adquisición de datos, lógica de control, comunicación basada en eventos y supervisión del estado de un dispositivo remoto. Además, la posibilidad de ajustar el umbral de sobrecarga en tiempo real y de estimar el costo de la energía consumida aporta un valor adicional en términos de seguridad y concientización energética.

---

## 10. Referencias

[1] Eclipse Mosquitto – An open source MQTT broker. Disponible en: <https://mosquitto.org/>  

[2] Wokwi – Online ESP32, Arduino & Microcontroller Simulator. Disponible en: <https://wokwi.com/>  

[3] Eclipse Paho MQTT – MQTT client library for Python. Disponible en: <https://www.eclipse.org/paho/>  

[4] Documentación de MQTT – Eclipse Foundation / OASIS.  

