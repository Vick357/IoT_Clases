from hx711 import HX711
from machine import Pin
import utime
import urequests
import json
import network

import socket

SERVER_IP = "10.200.3.107"   # ← cambia por la IP real del ESP32 servidor
SERVER_PORT = 12345

# Configuración para envío de comandos por cantidad
CANTIDAD_LIMITE = 3  # Número de monedas para enviar comando

ssid     = "WUSTA"
password = "USTA8600"

wifi = network.WLAN(network.STA_IF)
if not wifi.isconnected():
    print("Conectando a Wi-Fi...")
    wifi.active(True)
    wifi.connect(ssid, password)
    while not wifi.isconnected():
        utime.sleep(0.5)
print("Wi-Fi conectado, IP:", wifi.ifconfig()[0])

FIREBASE_URL = "https://clasificador-d7264-default-rtdb.firebaseio.com/IoT.json"


def actualizar_firebase(datos: dict):
    try:
        respuesta = urequests.patch(FIREBASE_URL, data=json.dumps(datos))
        print("HTTP status:", respuesta.status_code)      # <-- para ver por ejemplo 200 o 401, etc.
        print("Respuesta Firebase:", respuesta.text)      # <-- confirma qué devuelve Firebase
        respuesta.close()
    except Exception as e:
        print("Error al enviar datos a Firebase:", e)
        
        
def enviar_comando(comando: str, tipo_moneda: str):
    try:
        addr = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
        s = socket.socket()
        s.connect(addr)
        s.send(comando.encode())
        s.close()
        print(">> Comando '{}' enviado al servidor para {} monedas".format(comando, tipo_moneda))
    except Exception as e:
        print("Error al enviar comando al servidor:", e)

def verificar_y_enviar_comando(contador, tipo_moneda, comando):
    """
    Verifica si se alcanzó el límite y envía comando si es necesario
    """
    if contador > 0 and contador % CANTIDAD_LIMITE == 0:
        enviar_comando(comando, tipo_moneda)
        print("*** {} monedas de {} alcanzadas - Comando '{}' enviado ***".format(CANTIDAD_LIMITE, tipo_moneda, comando))
        return True
    return False

# Configuración del (o los) sensor(es) HX711 para peso
hx_1 = HX711(dout=17, pd_sck=18)  # Celda de carga 1 (moneda $1000)
hx_2 = HX711(dout=19, pd_sck=21)  # Celda de carga 2 (moneda $200 / monedas $50 viejas)
hx_3 = HX711(dout=22, pd_sck=23)  # Celda de carga 3 (monedas $50 nuevas)

print("Realizando tara, asegúrate de que la celda esté sin carga...")
hx_1.tare()
hx_2.tare()
hx_3.tare()
print("Tara completada.")

# Ajuste de escala tras calibrar
hx_1.set_scale(200)
hx_2.set_scale(200)
hx_3.set_scale(280)

# Sensores infrarrojos para detectar inserción de moneda
sensor_1000 = Pin(16, Pin.IN)  # GPIO16 → detección de moneda $1000
sensor_200  = Pin(4, Pin.IN)   # GPIO4  → detección de moneda $200 o $50 viejas
sensor_50   = Pin(15, Pin.IN)  # GPIO15 → detección de moneda $50 nuevas


# Moneda $1000
contador_1000     = 0
peso_total_1000   = 0.0
moneda_1          = 0  # para promedio dinámico
peso_promedio_1000= 0.0

# Moneda $200
contador_200           = 0
contador_200_nueva     = 0
contador_200_vieja     = 0
peso_total_200_nueva   = 0.0
peso_total_200_vieja   = 0.0
moneda_2               = 0  # para promedio dinámico
peso_promedio_200      = 0.0

# Moneda $50
contador_50           = 0
contador_50_nueva     = 0
contador_50_vieja     = 0
peso_total_50_nueva   = 0.0
peso_total_50_vieja   = 0.0
moneda_3              = 0  # para promedio dinámico
peso_promedio_50      = 0.0

# Tolerancia / límites para distinguir nuevas vs viejas
TOLERANCIA = 0.15  # 15%, no se usa directamente; puedes ajustar rangos
PESO_LIMITE_200 = 6.0
# en gramos: menos → nueva, más → vieja para moneda $200
PESO_LIMITE_50  = 3.5   # en gramos: menos → nueva (sensor 50), más → vieja (sensor 200)

# Peso por defecto para monedas $50 nuevas cuando la balanza marca 0
PESO_DEFECTO_50_NUEVA = 2.0  # gramos

# Contador de errores (monedas fuera de rango)
contador_error = 0

# Funciones para los sensores

def leer_peso_1000():
    try:
        return hx_1.get_units(times=3)
    except Exception as e:
        print("Error al leer sensor 1000:", e)
        return 0.0

def leer_peso_200():
    try:
        return hx_2.get_units(times=3)
    except Exception as e:
        print("Error al leer sensor 200:", e)
        return 0.0

def leer_peso_50():
    try:
        peso = hx_3.get_units(times=3)
        # Si el peso es 0 o muy cercano a 0, usar el peso por defecto
        if abs(peso) < 0.1:  # Tolerancia para considerar como "cero"
            print("Peso detectado como 0, usando peso por defecto: {:.2f}g".format(PESO_DEFECTO_50_NUEVA))
            return PESO_DEFECTO_50_NUEVA
        return peso
    except Exception as e:
        print("Error al leer sensor 50:", e)
        return PESO_DEFECTO_50_NUEVA  # Retornar peso por defecto en caso de error

# Bucle principal

print("\nSistema listo. Inserta monedas.\n")
print("INFORMACIÓN IMPORTANTE:")
print("Inserte la siguientes denominación de monedas:")
print("Monedas de 1000")
print("Monedas de 200")
print("Monedas de 50")
print("*** COMANDO SE ENVÍA CADA {} MONEDAS ***".format(CANTIDAD_LIMITE))
print("-"*50)

try:
    while True:

        # ─── Detectar moneda $1000 ─────────────────────────────────────────
        if sensor_1000.value() == 0:
            print("\n--- Sensor de moneda 1000 activado ---")
            moneda_1 += 1
            utime.sleep(1)  # Espera a que la moneda esté estable
            peso = leer_peso_1000()
            peso_promedio_1000 = peso / moneda_1
            print("Peso promedio $1000 por moneda: {:.2f} g".format(peso_promedio_1000))

            # Validar rango (solo nuevas)
            if 3.0 <= peso_promedio_1000 <= 20.0:
                contador_1000 += 1
                peso_total_1000 += peso_promedio_1000
                print("✓ Moneda de $1000 NUEVA registrada. Total $1000: {}".format(contador_1000))
                
                # *** ENVIAR COMANDO SOLO CADA 3 MONEDAS ***
                verificar_y_enviar_comando(contador_1000, "$1000", 'a')
                
            else:
                moneda_1 -= 1
                contador_error += 1
                print("✗ Moneda $1000 rechazada (fuera de rango).")

            # ── Actualizar Firebase tras cada evento
            datos_fb = {
                "ConteoGlobal": contador_1000 + contador_200 + contador_50,
                "Error": contador_error,
                "Monedas1000": contador_1000,
                "Monedas200": contador_200,
                "Monedas50": contador_50,
                # Desglose de monedas nuevas y viejas
                "Monedas1000Nuevas": contador_1000,
                "Monedas1000Viejas": 0,  # Las de $1000 solo son nuevas
                "Monedas200Nuevas": contador_200_nueva,
                "Monedas200Viejas": contador_200_vieja,
                "Monedas50Nuevas": contador_50_nueva,
                "Monedas50Viejas": contador_50_vieja,
                "PesoCaja1": peso_total_1000,  # Suma de pesos de $1000 (g)
                "PesoCaja2": peso_total_200_nueva + peso_total_200_vieja,  # suma pesos caja 2
                "PesoCaja3": peso_total_50_nueva + peso_total_50_vieja     # suma pesos caja 3
            }
            actualizar_firebase(datos_fb)

        # ─── Detectar moneda $200 O moneda $50 vieja (sensor 200) ────────────
        if sensor_200.value() == 0:
            print("\n--- Sensor de moneda 200 activado ---")
            moneda_2 += 1
            utime.sleep(1)
            peso = leer_peso_200()
            peso_promedio_200 = peso / moneda_2
            print("Peso promedio sensor 200: {:.2f} g".format(peso_promedio_200))

            # Caso: Moneda de $200 en rango general válido (4.7g – 9g)
            if 4.7 <= peso_promedio_200 <= 12:
                contador_200 += 1

                # Distinguir nueva vs vieja para $200
                if peso_promedio_200 < PESO_LIMITE_200:
                    contador_200_nueva += 1
                    peso_total_200_nueva += peso_promedio_200
                    print("✓ Moneda de $200 NUEVA registrada. Total $200: {}".format(contador_200))
                else:
                    contador_200_vieja += 1
                    peso_total_200_vieja += peso_promedio_200
                    print("✓ Moneda de $200 VIEJA registrada. Total $200: {}".format(contador_200))

                print("  $200 Nuevas: {} | $200 Viejas: {}".format(contador_200_nueva, contador_200_vieja))
                
                # *** ENVIAR COMANDO SOLO CADA 3 MONEDAS DE $200 ***
                verificar_y_enviar_comando(contador_200, "$200", 's')

            # Caso: Moneda de $50 vieja (2g – 4.3g) que cae en este sensor
            elif 2.0 <= peso_promedio_200 <= 4.3:
                contador_50 += 1
                contador_50_vieja += 1
                peso_total_50_vieja += peso_promedio_200
                print("✓ Moneda de $50 VIEJA registrada (sensor 200). Total $50: {}".format(contador_50))
                print("  $50 Nuevas: {} | $50 Viejas: {}".format(contador_50_nueva, contador_50_vieja))
                
                # *** ENVIAR COMANDO SOLO CADA 3 MONEDAS DE $50 ***
                verificar_y_enviar_comando(contador_50, "$50", 'd')

            else:
                moneda_2 -= 1
                contador_error += 1
                print("✗ Moneda rechazada en sensor 200 (fuera de rango).")

            # ── Actualizar Firebase
            datos_fb = {
                "ConteoGlobal": contador_1000 + contador_200 + contador_50,
                "Error": contador_error,
                "Monedas1000": contador_1000,
                "Monedas200": contador_200,
                "Monedas50": contador_50,
                # Desglose de monedas nuevas y viejas
                "Monedas1000Nuevas": contador_1000,
                "Monedas1000Viejas": 0,  # Las de $1000 solo son nuevas
                "Monedas200Nuevas": contador_200_nueva,
                "Monedas200Viejas": contador_200_vieja,
                "Monedas50Nuevas": contador_50_nueva,
                "Monedas50Viejas": contador_50_vieja,
                "PesoCaja1": peso_total_1000,
                "PesoCaja2": peso_total_200_nueva + peso_total_200_vieja,
                "PesoCaja3": peso_total_50_nueva + peso_total_50_vieja
            }
            actualizar_firebase(datos_fb)

        # ─── Detectar moneda $50 nuevas (sensor 50) ────────────────────────────
        if sensor_50.value() == 0:
            print("\n--- Sensor de moneda 50 activado ---")
            moneda_3 += 1
            utime.sleep(1)
            peso = leer_peso_50()  # Esta función ya maneja el caso de peso = 0
            peso_promedio_50 = peso / moneda_3
            print("Peso promedio sensor 50: {:.2f} g".format(peso_promedio_50))

            # En este sensor solo deben caer $50 nuevas
            if 0 <= peso_promedio_50 <= 16.0:
                contador_50 += 1
                contador_50_nueva += 1
                peso_total_50_nueva += peso_promedio_50
                print("✓ Moneda de $50 NUEVA registrada. Total $50: {}".format(contador_50))
                print("  $50 Nuevas: {} | $50 Viejas: {}".format(contador_50_nueva, contador_50_vieja))
                
                # *** ENVIAR COMANDO SOLO CADA 3 MONEDAS DE $50 ***
                verificar_y_enviar_comando(contador_50, "$50", 'd')
                
            else:
                moneda_3 -= 1
                contador_error += 1
                print("✗ Moneda de $50 rechazada (fuera de rango).")

            # ── Actualizar Firebase
            datos_fb = {
                "ConteoGlobal":                  contador_1000 + contador_200 + contador_50,
                "Error":                         contador_error,
                "Monedas1000":                   contador_1000,
                "Monedas200":                    contador_200,
                "Monedas50":                     contador_50,
                # Desglose de monedas nuevas y viejas
                "Monedas1000Nuevas":             contador_1000,
                "Monedas200Nuevas":              contador_200_nueva,
                "Monedas200Viejas":              contador_200_vieja,
                "Monedas50Nuevas":               contador_50_nueva,
                "Monedas50Viejas":               contador_50_vieja,
                "PesoCaja1":                     peso_total_1000,
                "PesoCaja2":                     peso_total_200_nueva + peso_total_200_vieja,
                "PesoCaja3":                     peso_total_50_nueva + peso_total_50_vieja
            }
            actualizar_firebase(datos_fb)

        utime.sleep(0.005)  # Leer sensores cada 5 ms para detección casi instantánea

# ──────────────────────────────────────────────────────────────────────────
# 4) AL HACER CTRL+C: IMPRIMIR RESUMEN FINAL Y ENVIAR DATOS FINALES A FIREBASE
# ──────────────────────────────────────────────────────────────────────────
except KeyboardInterrupt:
    print("\n" + "="*70)
    print("RESUMEN FINAL DEL CONTEO")
    print("="*70)

    # Totales simples
    print("\nTOTAL DE MONEDAS:")
    print("Monedas de $1000: {}".format(contador_1000))
    print("Monedas de $200: {}".format(contador_200))
    print("Monedas de $50: {}".format(contador_50))

    # Información de comandos enviados
    print("\n" + "-"*70)
    print("COMANDOS ENVIADOS:")
    comandos_1000 = contador_1000 // CANTIDAD_LIMITE
    comandos_200 = contador_200 // CANTIDAD_LIMITE
    comandos_50 = contador_50 // CANTIDAD_LIMITE
    
    print("Comando 'a' (monedas $1000): {} veces".format(comandos_1000))
    print("Comando 's' (monedas $200): {} veces".format(comandos_200))
    print("Comando 'd' (monedas $50): {} veces".format(comandos_50))

    # Desglose nuevas/viejas
    print("\n" + "-"*70)
    print("DESGLOSE POR CONDICIÓN (NUEVAS/VIEJAS):")

    print("\n$1000:")
    print("  Nuevas: {}".format(contador_1000))
    print("  Viejas: 0")
    if contador_1000 > 0:
        print("  Peso promedio: {:.2f} g".format(peso_total_1000/contador_1000))

    print("\n$200:")
    print("  Nuevas: {}".format(contador_200_nueva))
    print("  Viejas: {}".format(contador_200_vieja))
    if contador_200_nueva > 0:
        print("  Peso promedio nuevas: {:.2f} g".format(peso_total_200_nueva/contador_200_nueva))
    if contador_200_vieja > 0:
        print("  Peso promedio viejas: {:.2f} g".format(peso_total_200_vieja/contador_200_vieja))

    print("\n$50:")
    print("  Nuevas: {}".format(contador_50_nueva))
    print("  Viejas: {}".format(contador_50_vieja))
    if contador_50_nueva > 0:
        print("  Peso promedio nuevas: {:.2f} g".format(peso_total_50_nueva/contador_50_nueva))
    if contador_50_vieja > 0:
        print("  Peso promedio viejas: {:.2f} g".format(peso_total_50_vieja/contador_50_vieja))

    # Valores en pesos
    print("\n" + "-"*70)
    print("VALORES EN PESOS:")
    print("$1000 x {} = ${}".format(contador_1000, contador_1000 * 1000))
    print("$200 x {} = ${}".format(contador_200, contador_200 * 200))
    print("$50 x {} = ${}".format(contador_50, contador_50 * 50))

    # Total general
    valor_total = contador_1000*1000 + contador_200*200 + contador_50*50
    print("\n" + "="*70)
    print("TOTAL GENERAL: ${}".format(valor_total))
    print("="*70)

    # ── Enviar resumen final a Firebase (última actualización) ───────────────
    datos_fb = {
        "ConteoGlobal": contador_1000 + contador_200 + contador_50,
        "Error": contador_error,
        "Monedas1000": contador_1000,
        "Monedas200": contador_200,
        "Monedas50": contador_50,
        # Desglose final de monedas nuevas y viejas
        "Monedas1000Nuevas": contador_1000,
        "Monedas200Nuevas": contador_200_nueva,
        "Monedas200Viejas": contador_200_vieja,
        "Monedas50Nuevas": contador_50_nueva,
        "Monedas50Viejas": contador_50_vieja,
        "PesoCaja1": peso_total_1000,
        "PesoCaja2": peso_total_200_nueva + peso_total_200_vieja,
        "PesoCaja3": peso_total_50_nueva + peso_total_50_vieja
    }
    actualizar_firebase(datos_fb)
    print("Datos finales enviados a Firebase.")
