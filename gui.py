import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt
from datetime import datetime

# =============== CONFIG MQTT ==================
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
TOPIC_RELAY = "Smart_Plug-Relay"
TOPIC_POWER = "Power"

# =============== CONFIG LÓGICA ==================
UPDATE_INTERVAL_MS = 500          # cada cuánto se actualiza la GUI (ms)
COST_PER_KWH = 200.0              # ARS por kWh (puedes ajustar)
DEFAULT_OVERLOAD_THRESHOLD = 800.0  # W
STALE_TIMEOUT_S = 5.0             # segundos sin datos = se asume perdida de comunicación

# Estado de mediciones
last_power_str = "0.00"
last_power_val = 0.0
prev_power_val = 0.0
energy_Wh = 0.0

# Umbral de sobrecarga 
overload_threshold = DEFAULT_OVERLOAD_THRESHOLD
overload_detected = False 

# Monitoreo de comunicación con ESP32
last_msg_datetime = None   # última vez que llegó un mensaje Power
stale_reported = False     # para no spamear el log con el mismo mensaje

# =============== FUNCIONES AUXILIARES (LOG) ==================

def add_log(msg: str):
    """Agrega una línea al log con timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_listbox.insert(tk.END, f"[{timestamp}] {msg}")
    log_listbox.yview_moveto(1.0)

# =============== CALLBACKS MQTT ==================

def on_mqtt_connect(client, userdata, flags, rc):
    global last_msg_datetime, stale_reported
    if rc == 0:
        print("Conectado a MQTT ✅")
        status_var.set("Conectado a MQTT")
        client.subscribe(TOPIC_POWER)
        add_log("Conectado al broker MQTT")
        # reset de estado de comunicación
        last_msg_datetime = None
        stale_reported = False
    else:
        print("Error al conectar MQTT, código:", rc)
        status_var.set(f"Error MQTT: {rc}")
        add_log(f"Error de conexión MQTT: {rc}")

def on_mqtt_disconnect(client, userdata, rc):
    """Se llama cuando se pierde la conexión con el broker."""
    if rc != 0:
        status_var.set("Desconectado de MQTT (conexión perdida)")
        add_log("Desconectado del broker MQTT")
    else:
        status_var.set("Desconectado de MQTT (cerrado por la app)")
        add_log("Desconexión limpia del broker MQTT")

def on_mqtt_message(client, userdata, msg):
    global last_power_str, last_power_val, last_msg_datetime, stale_reported
    if msg.topic == TOPIC_POWER:
        payload = msg.payload.decode()
        last_power_str = payload
        try:
            last_power_val = float(payload)
        except ValueError:
            last_power_val = 0.0

        # Actualizamos timestamp de última lectura del ESP32
        last_msg_datetime = datetime.now()
        # Si estaba en estado "sin datos", lo limpiamos
        if stale_reported:
            stale_reported = False
            status_var.set("Conectado a MQTT (datos del ESP32 recibidos)")
            add_log("Se reanudó la recepción de datos del ESP32")

# =============== ACCIONES GUI ==================

def update_power_and_logic():
    """Actualiza potencia, sobrecarga, energía y estado de comunicación."""
    global prev_power_val, overload_detected, energy_Wh, stale_reported

    # Mostrar potencia actual
    power_var.set(f"{last_power_str} W")

    # ===== Integración de energía (Wh) =====
    dt_s = UPDATE_INTERVAL_MS / 1000.0
    # Energía = Potencia (W) * tiempo (h)
    energy_Wh += last_power_val * (dt_s / 3600.0)
    energy_kWh = energy_Wh / 1000.0
    energy_var.set(f"{energy_kWh:.3f} kWh")

    cost_est = energy_kWh * COST_PER_KWH
    cost_var.set(f"${cost_est:,.2f} ARS")

    # ===== Lógica de sobrecarga visual =====
    if last_power_val > overload_threshold:
        overload_var.set(
            f"⚠ Sobrecarga: {last_power_val:.0f} W "
            f"(límite {overload_threshold:.0f} W)"
        )
        overload_label.config(foreground="red")
        overload_detected = True
    else:
        overload_var.set("Sin sobrecarga")
        overload_label.config(foreground="gray")

    # ===== Detección de apagado automático por sobrecarga =====
    if (
        overload_detected and
        last_power_val == 0.0 and
        prev_power_val > overload_threshold
    ):
        relay_state_var.set("APAGADO (por sobrecarga)")
        relay_state_label.config(foreground="red")
        last_event_var.set("Último evento: Apagado automático por sobrecarga")
        add_log("Apagado automático por sobrecarga")
        overload_detected = False

    # ===== Monitoreo de comunicación con el ESP32 =====
    # 1) Si no estamos conectados al broker
    if not mqtt_client.is_connected():
        status_var.set("Desconectado de MQTT")
        # No marcamos SIN COMUNICACIÓN aquí, porque puede ser solo caída de red
    else:
        # 2) Broker OK: chequear si el ESP32 dejó de enviar datos
        if last_msg_datetime is not None:
            delta_s = (datetime.now() - last_msg_datetime).total_seconds()
            if delta_s > STALE_TIMEOUT_S:
                # > N segundos sin datos: asumimos pérdida de comunicación con el equipo
                status_var.set("Sin datos del ESP32 (timeout)")
                relay_state_var.set("SIN COMUNICACIÓN")
                relay_state_label.config(foreground="orange")
                if not stale_reported:
                    add_log(
                        f"Sin datos del ESP32 desde hace {int(delta_s)} s "
                        "(timeout de lecturas)"
                    )
                    stale_reported = True

    # Guardamos para la próxima iteración
    prev_power_val = last_power_val

    root.after(UPDATE_INTERVAL_MS, update_power_and_logic)

def send_on():
    """Enciende el enchufe (publica '1')."""
    mqtt_client.publish(TOPIC_RELAY, "1")
    relay_state_var.set("ENCENDIDO")
    relay_state_label.config(foreground="green")
    last_event_var.set("Último evento: Encendido manual")
    add_log("Encendido manual")

def send_off():
    """Apaga el enchufe (publica '0')."""
    mqtt_client.publish(TOPIC_RELAY, "0")
    relay_state_var.set("APAGADO")
    relay_state_label.config(foreground="red")
    last_event_var.set("Último evento: Apagado manual")
    add_log("Apagado manual")

def aplicar_umbral():
    """Lee el umbral de la entrada y lo aplica (GUI + ESP32)."""
    global overload_threshold
    txt = entry_umbral.get().strip()
    try:
        val = float(txt)
        if val <= 0:
            raise ValueError
        overload_threshold = val

        mqtt_client.publish("Smart_Plug/Overload_W", str(overload_threshold))

        add_log(f"Nuevo umbral de sobrecarga: {overload_threshold:.0f} W (enviado al ESP32)")
        status_var.set(f"Umbral sobrecarga = {overload_threshold:.0f} W")
    except ValueError:
        status_var.set("Error: umbral inválido")
        add_log("Intento de configurar umbral inválido")


def reset_energy():
    """Resetea el contador de energía y costo."""
    global energy_Wh
    energy_Wh = 0.0
    energy_var.set("0.000 kWh")
    cost_var.set("$0.00 ARS")
    add_log("Se reseteó el contador de energía")

# =============== GUI (TKINTER) ==================

root = tk.Tk()
root.title("Smart Plug - Grupo 10")
root.geometry("600x420")

style = ttk.Style(root)
style.configure("TButton", font=("Segoe UI", 10))
style.configure("TLabel", font=("Segoe UI", 10))

title_label = ttk.Label(root, text="Enchufe inteligente (MQTT)", font=("Segoe UI", 13, "bold"))
title_label.pack(pady=5)

# ----- Estado de conexión -----
status_var = tk.StringVar(value="Conectando a MQTT...")
status_label = ttk.Label(root, textvariable=status_var)
status_label.pack(pady=(0, 5))

# ----- Frame superior (control + medición + config) -----
top_frame = ttk.Frame(root)
top_frame.pack(fill="x", expand=False, padx=10, pady=5)

# ----- Columna 1: Control -----
control_frame = ttk.LabelFrame(top_frame, text="Control")
control_frame.pack(side="left", fill="y", expand=False, padx=(0, 5), pady=5)

btn_on = ttk.Button(control_frame, text="Encender", command=send_on)
btn_on.pack(padx=5, pady=(10, 5), fill="x")

btn_off = ttk.Button(control_frame, text="Apagar", command=send_off)
btn_off.pack(padx=5, pady=5, fill="x")

relay_state_var = tk.StringVar(value="APAGADO")
relay_state_label = ttk.Label(
    control_frame,
    textvariable=relay_state_var,
    font=("Segoe UI", 11, "bold"),
    foreground="red"
)
relay_state_label.pack(padx=5, pady=(10, 5))

last_event_var = tk.StringVar(value="Último evento: —")
last_event_label = ttk.Label(control_frame, textvariable=last_event_var, font=("Segoe UI", 9))
last_event_label.pack(pady=(5, 10))

# ----- Columna 2: Medición -----
med_frame = ttk.LabelFrame(top_frame, text="Medición")
med_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

ttk.Label(med_frame, text="Potencia actual:").pack(pady=(8, 2))
power_var = tk.StringVar(value="0.00 W")
power_label = ttk.Label(med_frame, textvariable=power_var, font=("Segoe UI", 14, "bold"))
power_label.pack(pady=(0, 10))

overload_var = tk.StringVar(value="Sin sobrecarga")
overload_label = ttk.Label(med_frame, textvariable=overload_var, font=("Segoe UI", 10))
overload_label.pack(pady=(0, 5))

ttk.Label(med_frame, text="Energía acumulada:").pack(pady=(8, 2))
energy_var = tk.StringVar(value="0.000 kWh")
energy_label = ttk.Label(med_frame, textvariable=energy_var, font=("Segoe UI", 11))
energy_label.pack(pady=(0, 5))

ttk.Label(med_frame, text="Costo estimado:").pack(pady=(4, 2))
cost_var = tk.StringVar(value="$0.00 ARS")
cost_label = ttk.Label(med_frame, textvariable=cost_var, font=("Segoe UI", 11, "bold"))
cost_label.pack(pady=(0, 5))

btn_reset_energy = ttk.Button(med_frame, text="Reset energía", command=reset_energy)
btn_reset_energy.pack(pady=(5, 5))

# ----- Columna 3: Configuración -----
config_frame = ttk.LabelFrame(top_frame, text="Configuración")
config_frame.pack(side="right", fill="y", expand=False, padx=(5, 0), pady=5)

# Umbral de sobrecarga
ttk.Label(config_frame, text="Umbral sobrecarga (W):").pack(pady=(8, 2))
entry_umbral = ttk.Entry(config_frame)
entry_umbral.pack(padx=5, pady=(0, 4), fill="x")
entry_umbral.insert(0, str(DEFAULT_OVERLOAD_THRESHOLD))

btn_aplicar_umbral = ttk.Button(config_frame, text="Aplicar umbral", command=aplicar_umbral)
btn_aplicar_umbral.pack(padx=5, pady=(0, 8), fill="x")

# ----- Frame inferior: Log de eventos -----
log_frame = ttk.LabelFrame(root, text="Log de eventos")
log_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

log_listbox = tk.Listbox(log_frame, height=8, font=("Consolas", 9))
log_listbox.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)

log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=log_listbox.yview)
log_scroll.pack(side="right", fill="y", padx=(0, 5), pady=5)
log_listbox.config(yscrollcommand=log_scroll.set)

# =============== MQTT ==================
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_disconnect = on_mqtt_disconnect
mqtt_client.on_message = on_mqtt_message

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# Empezar a actualizar la potencia, energía y sobrecarga
update_power_and_logic()

root.mainloop()
