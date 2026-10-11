# -*- coding: utf-8 -*-
"""
PickABoo - Trailer - ESCENA 1 (version 2): el telefono que suena, con los
muebles y materiales del entorno Entornos/EntornoTelefono.

Misma idea y misma animacion que escena1_oficina.py, pero en vez de cajas usa
las piezas de entornoTelefono_LogoNuevo.mb recolocadas segun el storyboard:
pared larga, aparador con el telefono, puerta a la derecha y poster del logo a
la izquierda. El archivo original del entorno NO se modifica: se abre, se
reorganiza y se guarda con otro nombre en animaciones/escenas/.

Como ejecutarlo dentro de Maya:
    Windows > General Editors > Script Editor, pestana Python, y pegar:
        exec(open(r"C:/Users/Alejandro/Desktop/Modelos3DMaya/animaciones/scripts/escena1_oficina_v2.py", encoding="utf-8").read())

OJO: el script abre otra escena. Si tienes cambios sin guardar se detiene para
no perderlos; guarda primero y vuelve a ejecutar.
"""
import os
import sys

import maya.cmds as cmds

# Con mayapy (Maya sin ventana) hay que arrancar el motor a mano.
_SIN_VENTANA = not hasattr(cmds, "polyCube")
if _SIN_VENTANA:
    import maya.standalone
    maya.standalone.initialize(name="python")

# =============================================================================
# AJUSTES. Unidades en centimetros, en las coordenadas del entorno original:
# la pared del fondo esta en Z=-150 y el telefono alrededor de X=24.
# =============================================================================
try:
    ANIMACIONES = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
except NameError:
    ANIMACIONES = "C:/Users/Alejandro/Desktop/Modelos3DMaya/animaciones"
ENTORNO = os.path.dirname(ANIMACIONES) + "/Entornos/EntornoTelefono/entornoTelefono_LogoNuevo.mb"
SALIDA = ANIMACIONES + "/escenas/escena1_oficina_v2.mb"

F_INICIO = 1
F_FIN_PANEO = 168      # 7 s: la camara termina de desplazarse a la izquierda
F_FIN = 264            # 11 s: la camara termina de acercarse al logo

# Posicion de la camara (x, y, z) y su inclinacion en grados (negativo = mira
# hacia abajo) en cada momento clave.
CAM_INICIO = (105.0, 135.0, 200.0, -6.0)     # se ve el aparador y la puerta
CAM_FIN_PANEO = (-82.0, 135.0, 200.0, -6.0)  # el poster asoma por la izquierda
CAM_FINAL = (-212.0, 180.0, 70.0, 0.0)       # el poster llena el encuadre

# Cada pareja es (fotograma en que empieza, fotograma en que acaba) un "piiip".
TIMBRAZOS = [(1, 14), (22, 35), (60, 73), (81, 94)]
# Desde aqui la luz se queda fija: esta sonando el mensaje del contestador.
LUZ_FIJA_DESDE = 110

ANCHO_MODULO = 350.0   # ancho de la habitacion original; la pared se repite 3 veces
POSTER_X, POSTER_ESCALA = -212.0, 1.6
PUERTA_X = 243.0
CUADRO_X = 140.0


def centro(nodo):
    x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(nodo)
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)


def quitar_hijos(grupo, conservar):
    """Borra los hijos de 'grupo' cuyo nombre no este en 'conservar'."""
    for hijo in cmds.listRelatives(grupo, children=True, fullPath=True) or []:
        if hijo.split("|")[-1] not in conservar:
            cmds.delete(hijo)


# =============================================================================
# 1. ABRIR EL ENTORNO ORIGINAL (solo lectura: se guardara con otro nombre)
# =============================================================================
if cmds.file(query=True, modified=True):
    raise RuntimeError("Tienes cambios sin guardar en Maya. Guarda la escena y vuelve a ejecutar el script.")
cmds.loadPlugin("mtoa", quiet=True)  # Arnold: los materiales del entorno son suyos
cmds.file(ENTORNO, open=True, force=True, ignoreVersion=True)
cmds.file(rename=SALIDA)  # desde ya, para que un Ctrl+S nunca pise el original

# =============================================================================
# 2. QUITAR LO QUE NO ENCAJA CON EL STORYBOARD
# La habitacion original es cerrada y de 3,5 m; el plano necesita una pared
# larga para que la camara pueda desplazarse, sin paredes laterales ni techo.
# =============================================================================
quitar_hijos("Paredes", ("Pared_Fondo", "Zocalos_Y_Revestimiento"))
quitar_hijos("Zocalos_Y_Revestimiento", ("Panelado_Fondo", "Cornisa_Fondo"))
cmds.delete("Techo", "Ventana", "Cortinas", "Luces", "Camaras")

# =============================================================================
# 3. PARED LARGA: el tramo de pared + zocalo + cornisa + suelo, repetido a
# izquierda y derecha.
# =============================================================================
# La pared mide 370 (se metia en las esquinas); se ajusta a 350 para que los
# tramos repetidos no se monten unos sobre otros.
cmds.scale(ANCHO_MODULO / 370.0, 1, 1, "Pared_Fondo", pivot=(0, 0, 0))
modulo = cmds.group("Pared_Fondo", "Panelado_Fondo", "Cornisa_Fondo", "Tarima_Madera", name="Modulo_Sala_Centro")
for nombre, lado in (("Modulo_Sala_Izquierda", -1), ("Modulo_Sala_Derecha", 1)):
    copia = cmds.duplicate(modulo, name=nombre)[0]
    cmds.move(lado * ANCHO_MODULO, 0, 0, copia, relative=True)

# =============================================================================
# 4. RECOLOCAR PUERTA, POSTER DEL LOGO Y CUADRO SOBRE LA PARED DEL FONDO
# =============================================================================
# Puerta: estaba en la pared de enfrente (detras de la camara). Se gira media
# vuelta y se lleva a la derecha del aparador.
cx, cy, cz = centro("Puerta_Habitacion")
cmds.rotate(0, 180, 0, "Puerta_Habitacion", pivot=(cx, 0, cz))
cmds.move(PUERTA_X - cx, 0, -143 - cz, "Puerta_Habitacion", relative=True)

# Poster del logo: estaba justo encima del telefono. En el storyboard el logo
# queda a la izquierda, y mas grande para que llene el plano final.
cx, cy, cz = centro("Logo_Pick_A_Boo")
cmds.scale(POSTER_ESCALA, POSTER_ESCALA, 1, "Logo_Pick_A_Boo", pivot=(cx, cy, cz))
cmds.move(POSTER_X - cx, 0, 0.3, "Logo_Pick_A_Boo", relative=True)

# Cuadro botanico: estaba en la pared derecha; pasa al fondo, sobre la silla.
cx, cy, cz = centro("Cuadros")
cmds.rotate(0, 90, 0, "Cuadros", pivot=(cx, cy, cz))
cmds.move(CUADRO_X - cx, 0, -147.5 - cz, "Cuadros", relative=True)

# Reloj: se acerca al aparador para que no se cuele en el plano final del logo.
cmds.move(44, 0, 0, "Reloj_Pared", relative=True)

# =============================================================================
# 5. LUCES: oficina al anochecer. Se conserva la lampara del aparador (va
# dentro de su grupo) y se anade un relleno frio para que se lea todo.
# =============================================================================
ambiente = cmds.ambientLight(name="LUZ_ambiente", rgb=(0.75, 0.82, 1.0), intensity=0.3)
relleno = cmds.directionalLight(name="LUZ_relleno", rgb=(0.85, 0.9, 1.0), intensity=0.35)
cmds.rotate(-35, 20, 0, cmds.listRelatives(relleno, parent=True)[0])
# La lampara venia ajustada para render con Arnold; en el visor quemaba la imagen.
cmds.setAttr("Forma_Luz_Lampara.intensity", 0.5)

# Luz roja del contestador. Con decayRate=2 pierde fuerza con la distancia y
# solo tine lo que hay alrededor del telefono.
x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox("Base_Y_Contestador")
luz_led = cmds.pointLight(name="LUZ_led", rgb=(1.0, 0.1, 0.05), intensity=0.0)
luz_led_t = cmds.listRelatives(luz_led, parent=True)[0]
cmds.setAttr(luz_led + ".decayRate", 2)
cmds.move((x0 + x1) / 2.0, y1 + 8, z1 - 4, luz_led_t)
cmds.group([cmds.listRelatives(n, parent=True)[0] for n in (ambiente, relleno, luz_led)], name="GRP_luces_animacion")

# =============================================================================
# 6. AJUSTES DE TIEMPO E IMAGEN
# =============================================================================
cmds.currentUnit(time="film")  # "film" = 24 fotogramas por segundo
cmds.playbackOptions(minTime=F_INICIO, maxTime=F_FIN, animationStartTime=F_INICIO, animationEndTime=F_FIN)
cmds.setAttr("defaultResolution.width", 1920)
cmds.setAttr("defaultResolution.height", 1080)
cmds.setAttr("defaultResolution.deviceAspectRatio", 1920.0 / 1080.0)
cmds.setAttr("defaultRenderGlobals.startFrame", F_INICIO)
cmds.setAttr("defaultRenderGlobals.endFrame", F_FIN)
cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)  # bordes suavizados en visor y playblast

# =============================================================================
# 7. CAMARA Y SU ANIMACION
# Un keyframe guarda "en este fotograma, este valor". Maya rellena lo de en medio.
# =============================================================================
cam = cmds.camera(focalLength=35, horizontalFilmAperture=1.417, verticalFilmAperture=0.797,
                  nearClipPlane=1, farClipPlane=5000)[0]
cam = cmds.rename(cam, "CAM_escena1")
cam_forma = cmds.listRelatives(cam, shapes=True)[0]
cmds.setAttr(cam_forma + ".displayResolution", 1)  # dibuja el marco del encuadre
cmds.setAttr(cam_forma + ".renderable", 1)
cmds.setAttr("perspShape.renderable", 0)

CANALES_CAM = ("translateX", "translateY", "translateZ", "rotateX")
for fotograma, valores in ((F_INICIO, CAM_INICIO), (F_FIN_PANEO, CAM_FIN_PANEO), (F_FIN, CAM_FINAL)):
    for canal, valor in zip(CANALES_CAM, valores):
        cmds.setKeyframe(cam, attribute=canal, time=fotograma, value=valor)

# Tangentes: "auto" suaviza el paso por el keyframe del medio para que la camara
# no se pare en seco; "flat" al principio y al final hace que arranque y frene suave.
cmds.keyTangent(cam, attribute=CANALES_CAM, inTangentType="auto", outTangentType="auto")
cmds.keyTangent(cam, attribute=CANALES_CAM, time=(F_INICIO, F_INICIO), inTangentType="flat", outTangentType="flat")
cmds.keyTangent(cam, attribute=CANALES_CAM, time=(F_FIN, F_FIN), inTangentType="flat", outTangentType="flat")

# =============================================================================
# 8. ANIMACION DEL TELEFONO: indicador rojo, luz y vibracion en cada timbrazo
# =============================================================================
LUZ_ENCENDIDA = 600.0  # alta porque la luz se atenua con el cuadrado de la distancia
INDICADOR = "Material_Indicador_Rojo"  # el material del piloto del contestador
TELEFONO = "Telefono_Contestador"
# El telefono vibra girando alrededor del centro de su base.
cmds.xform(TELEFONO, worldSpace=True, pivots=((x0 + x1) / 2.0, y0, (z0 + z1) / 2.0))


def luz(fotograma, encendida):
    cmds.setKeyframe(INDICADOR, attribute="emission", time=fotograma, value=1.0 if encendida else 0.0)
    cmds.setKeyframe(luz_led, attribute="intensity", time=fotograma, value=LUZ_ENCENDIDA if encendida else 0.0)


luz(F_INICIO, False)
for empieza, acaba in TIMBRAZOS:
    luz(empieza, True)
    luz(acaba + 1, False)
    # Vibracion: el telefono se inclina a un lado y a otro cada 2 fotogramas.
    cmds.setKeyframe(TELEFONO, attribute="rotateZ", time=empieza - 1, value=0)
    for i, fotograma in enumerate(range(empieza, acaba + 1, 2)):
        cmds.setKeyframe(TELEFONO, attribute="rotateZ", time=fotograma, value=1.5 if i % 2 == 0 else -1.5)
    cmds.setKeyframe(TELEFONO, attribute="rotateZ", time=acaba + 1, value=0)
luz(LUZ_FIJA_DESDE, True)

# "step" = el valor salta de golpe en vez de ir subiendo poco a poco: una luz
# que parpadea se enciende y se apaga, no hace fundidos.
cmds.keyTangent(INDICADOR, attribute="emission", outTangentType="step")
cmds.keyTangent(luz_led, attribute="intensity", outTangentType="step")

# =============================================================================
# 9. GUARDAR
# =============================================================================
cmds.currentTime(F_INICIO)
cmds.select(clear=True)
if not os.path.isdir(os.path.dirname(SALIDA)):
    os.makedirs(os.path.dirname(SALIDA))
cmds.file(save=True, type="mayaBinary")
print("Escena guardada en " + SALIDA)

if _SIN_VENTANA:
    # Arnold falla al cerrar Maya sin ventana; se sale directamente, ya esta guardado.
    sys.stdout.flush()
    os._exit(0)
else:
    # Dentro de Maya: mirar por la camara del plano con luces y texturas activas.
    for panel in cmds.getPanel(type="modelPanel"):
        if cmds.modelPanel(panel, query=True, camera=True).startswith("persp"):
            cmds.lookThru(panel, cam)
            cmds.modelEditor(panel, edit=True, displayAppearance="smoothShaded",
                             displayTextures=True, displayLights="all")
