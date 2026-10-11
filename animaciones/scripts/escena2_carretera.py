# -*- coding: utf-8 -*-
"""
PickABoo - Trailer - ESCENA 2: la furgoneta por el bosque hasta la casa.

Usa el entorno Entornos/entornoCarreteraConCasa_EntradaLarga.mb (enlazado como
referencia, no se copia ni se modifica) y la furgoneta de Modelos/Furgoneta.
Crea el recorrido, las cinco camaras de los planos y toda la animacion, y
guarda animaciones/escenas/escena2_carretera.mb

Como ejecutarlo dentro de Maya:
    Windows > General Editors > Script Editor, pestana Python, y pegar:
        exec(open(r"C:/Users/Alejandro/Desktop/Modelos3DMaya/animaciones/scripts/escena2_carretera.py", encoding="utf-8").read())

OJO: el script empieza una escena nueva. Si tienes cambios sin guardar se
detiene para no perderlos; guarda primero y vuelve a ejecutar.
"""
import math
import os
import sys

import maya.cmds as cmds

# Con mayapy (Maya sin ventana) hay que arrancar el motor a mano.
_SIN_VENTANA = not hasattr(cmds, "polyCube")
if _SIN_VENTANA:
    import maya.standalone
    maya.standalone.initialize(name="python")

# =============================================================================
# AJUSTES. Unidades en centimetros, en las coordenadas del entorno:
# la carretera va a lo largo de Z, la casa queda al este (+X) y el suelo de la
# carretera esta en Y=-53.
# =============================================================================
try:
    ANIMACIONES = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
except NameError:
    ANIMACIONES = "C:/Users/Alejandro/Desktop/Modelos3DMaya/animaciones"
REPO = os.path.dirname(ANIMACIONES)
ENTORNO = REPO + "/Entornos/entornoCarreteraConCasa_EntradaLarga.mb"
FURGONETA = REPO + "/Modelos/Furgoneta/boorgoneta_final.mb"
TEXTURAS_FURGONETA = REPO + "/Modelos/Furgoneta/sourceimages"
SALIDA = ANIMACIONES + "/escenas/escena2_carretera.mb"

ESCALA_FURGONETA = 200.0   # el modelo mide 2 cm de largo; asi queda en 4 m
RADIO_RUEDA = 0.24 * ESCALA_FURGONETA

CARRIL_X = -2985.0         # centro del carril derecho yendo hacia -Z
SUELO_Y = -53.0
Z_INICIO = 6000.0          # donde empieza el recorrido, en el tramo largo
RADIO_GIRO = 260.0
CAMINO_Z = -16.0           # eje del camino de grava que lleva a la casa
PARADA_X = -2420.0         # donde queda el centro de la furgoneta al frenar
FIN_X = -2300.0            # final de la curva guia (un poco mas alla de la parada)

# Planos: (nombre, primer fotograma, ultimo fotograma).
PLANOS = [("A_logo", 1, 96), ("B_lateral", 97, 180), ("C_aerea", 181, 264),
          ("D_giro", 265, 336), ("E_frenazo", 337, 390)]
F_FIN = PLANOS[-1][2]
F_PARADA = 366             # fotograma en que la furgoneta queda parada

# Tramo de carretera (Z de salida, Z de llegada) que recorre en los planos A, B y C.
# Como hay corte entre planos, en cada uno se coloca donde mejor se ve.
TRAMO_A = (5900.0, 2800.0)
TRAMO_B = (3300.0, 1700.0)
TRAMO_C = (2700.0, 800.0)
Z_INICIO_GIRO_PLANO_D = 1200.0

# Centro del logo en el lateral, medido desde el centro de la furgoneta a ras
# de suelo: (altura, posicion a lo largo; negativo = hacia atras).
LOGO_ALTO, LOGO_LARGO = 126.0, -95.0


def apuntar(camara, objetivo):
    """Gira la camara para que mire al punto 'objetivo' (x, y, z)."""
    px, py, pz = cmds.xform(camara, query=True, worldSpace=True, translation=True)
    dx, dy, dz = objetivo[0] - px, objetivo[1] - py, objetivo[2] - pz
    cmds.setAttr(camara + ".rotateY", math.degrees(math.atan2(-dx, -dz)))
    cmds.setAttr(camara + ".rotateX", math.degrees(math.atan2(dy, math.hypot(dx, dz))))


def crear_camara(nombre, focal=35):
    cam = cmds.camera(focalLength=focal, horizontalFilmAperture=1.417, verticalFilmAperture=0.797,
                      nearClipPlane=10, farClipPlane=100000)[0]
    cam = cmds.rename(cam, nombre)
    cmds.setAttr(cmds.listRelatives(cam, shapes=True)[0] + ".displayResolution", 1)
    return cam


def clave(nodo, atributo, fotograma, valor):
    cmds.setKeyframe(nodo, attribute=atributo, time=fotograma, value=valor)


# =============================================================================
# 1. ESCENA NUEVA + ENTORNO COMO REFERENCIA
# Una referencia es un enlace al archivo del entorno: esta escena no lo copia,
# asi pesa poco y, si el entorno cambia, aqui se actualiza solo.
# =============================================================================
if cmds.file(query=True, modified=True):
    raise RuntimeError("Tienes cambios sin guardar en Maya. Guarda la escena y vuelve a ejecutar el script.")
cmds.file(new=True, force=True)
cmds.loadPlugin("mtoa", quiet=True)  # Arnold: parte de los materiales son suyos
cmds.file(ENTORNO, reference=True, namespace="ENT", ignoreVersion=True)

# El visor de Maya solo usa 16 luces a la vez y la casa tiene unas 40 dentro.
# Se ocultan las interiores para que cuenten la luna, los faroles y los faros.
for forma in cmds.ls(lights=True, long=True):
    if "|ENT:CASA|" in forma:
        cmds.setAttr(cmds.listRelatives(forma, parent=True, fullPath=True)[0] + ".visibility", 0)
# La cupula de cielo es de Arnold; en el visor solo lava la imagen. Vuelve a
# hacerla visible si algun dia se renderiza con Arnold.
for cupula in cmds.ls(type="aiSkyDomeLight", long=True):
    cmds.setAttr(cmds.listRelatives(cupula, parent=True, fullPath=True)[0] + ".visibility", 0)
cmds.setAttr("hardwareRenderingGlobals.maxHardwareLights", 16)

# Las luces del entorno estan medidas para Arnold. En el visor la luna quemaba
# las copas de los arboles y los faroles no se notaban: se reajustan aqui (son
# cambios sobre la referencia, el archivo del entorno no se toca).
for luna in cmds.ls(type="directionalLight", long=True):
    cmds.setAttr(luna + ".intensity", 0.4)
    if "Relleno" in luna:
        cmds.setAttr(luna + ".useDepthMapShadows", 0)
        cmds.setAttr(luna + ".useRayTraceShadows", 0)
for farol in cmds.ls("ENT:Luz_Farol_Maya_*", type="pointLight", long=True):
    cmds.setAttr(farol + ".decayRate", 1)
    cmds.setAttr(farol + ".intensity", 220)
ambiente = cmds.ambientLight(name="LUZ_ambiente_noche", rgb=(0.45, 0.55, 0.9), intensity=0.35)

# Cielo nocturno: una esfera enorme azul oscuro que envuelve todo. Sin ella el
# fondo del visor sale gris o blanco.
cielo = cmds.polySphere(name="CIELO_noche", radius=45000, subdivisionsX=24, subdivisionsY=12)[0]
cmds.move(-1000, 0, 1000, cielo)
mat_cielo = cmds.shadingNode("surfaceShader", asShader=True, name="MAT_cielo_noche")
cmds.setAttr(mat_cielo + ".outColor", 0.012, 0.022, 0.06, type="double3")
sg_cielo = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="MAT_cielo_nocheSG")
cmds.connectAttr(mat_cielo + ".outColor", sg_cielo + ".surfaceShader")
cmds.sets(cielo, edit=True, forceElement=sg_cielo)
cielo_forma = cmds.listRelatives(cielo, shapes=True)[0]
cmds.setAttr(cielo_forma + ".castsShadows", 0)
cmds.setAttr(cielo_forma + ".receiveShadows", 0)

# =============================================================================
# 2. LA FURGONETA
# Se importa (no referencia) porque hay que limpiarla: trae animacion suelta y
# las texturas apuntan a carpetas de otro ordenador.
# =============================================================================
nuevos = cmds.file(FURGONETA, i=True, returnNewNodes=True, namespace="FUR", ignoreVersion=True)
curvas_viejas = cmds.ls(nuevos, type="animCurve")
if curvas_viejas:
    cmds.delete(curvas_viejas)
for tex in cmds.ls(nuevos, type="file"):
    local = TEXTURAS_FURGONETA + "/" + os.path.basename(cmds.getAttr(tex + ".fileTextureName"))
    if os.path.isfile(local):
        cmds.setAttr(tex + ".fileTextureName", local, type="string")

# Tres grupos, uno dentro de otro, cada uno con un trabajo:
#   VAN_ruta    -> lo mueve el recorrido por la carretera
#   VAN_frenada -> el cabeceo y el derrape del frenazo
#   VAN_escala  -> agranda el modelo y lo apoya en el suelo, centrado
x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox("FUR:FURGONETA")
van_escala = cmds.group("FUR:FURGONETA", name="VAN_escala")
cmds.xform(van_escala, pivots=(0, 0, 0), worldSpace=True)
cmds.scale(ESCALA_FURGONETA, ESCALA_FURGONETA, ESCALA_FURGONETA, van_escala)
cmds.move(-(x0 + x1) / 2.0 * ESCALA_FURGONETA, -y0 * ESCALA_FURGONETA, -(z0 + z1) / 2.0 * ESCALA_FURGONETA, van_escala)
van_frenada = cmds.group(van_escala, name="VAN_frenada")
cmds.xform(van_frenada, pivots=(0, 0, 0), worldSpace=True)
van_ruta = cmds.group(van_frenada, name="VAN_ruta")
cmds.xform(van_ruta, pivots=(0, 0, 0), worldSpace=True)
LARGO = (z1 - z0) * ESCALA_FURGONETA
ANCHO = (x1 - x0) * ESCALA_FURGONETA

# Faros: dos focos en el morro. decayRate=1 hace que la luz pierda fuerza con
# la distancia, como un faro de verdad.
faros = []
for lado in (-1, 1):
    foco = cmds.spotLight(name="LUZ_faro_%s" % ("izq" if lado < 0 else "der"), rgb=(1.0, 0.93, 0.75),
                          intensity=600.0, coneAngle=55, penumbra=12)
    foco_t = cmds.listRelatives(foco, parent=True)[0]
    cmds.setAttr(foco + ".decayRate", 1)
    cmds.move(lado * ANCHO * 0.27, 90, LARGO / 2.0, foco_t)
    cmds.rotate(-7, 180, 0, foco_t)  # un foco mira a -Z; se gira hacia el frente y algo abajo
    faros.append(foco_t)
cmds.parent(faros, van_frenada)

# Relleno suave que viaja con la furgoneta por el lado de la camara, para que
# el lateral y el logo se lean de noche.
relleno_van = cmds.pointLight(name="LUZ_relleno_furgoneta", rgb=(0.8, 0.88, 1.0), intensity=320.0)
relleno_van_t = cmds.listRelatives(relleno_van, parent=True)[0]
cmds.setAttr(relleno_van + ".decayRate", 1)
cmds.move(500, 250, 100, relleno_van_t)
cmds.parent(relleno_van_t, van_ruta)

# =============================================================================
# 3. EL RECORRIDO: una curva guia sobre la carretera y el camino de la casa
# =============================================================================
z_giro = CAMINO_Z + RADIO_GIRO          # donde deja de ir recta
centro_x = CARRIL_X + RADIO_GIRO        # centro del arco del giro a la derecha
puntos = [(CARRIL_X, SUELO_Y, z) for z in (Z_INICIO, 5000, 4000, 3000, 2000, 1200, 700, 450, z_giro)]
for grados in (15, 30, 45, 60, 75, 90):
    a = math.radians(grados)
    puntos.append((centro_x - RADIO_GIRO * math.cos(a), SUELO_Y, z_giro - RADIO_GIRO * math.sin(a)))
# El camino de grava esta 4 cm mas alto que el asfalto.
puntos += [(centro_x + 120, SUELO_Y + 2, CAMINO_Z), (PARADA_X, SUELO_Y + 4, CAMINO_Z), (FIN_X, SUELO_Y + 4, CAMINO_Z)]
ruta = cmds.curve(name="RUTA_furgoneta", editPoint=puntos, degree=3)
LONGITUD = cmds.arclen(ruta)

# El motion path sujeta la furgoneta a la curva y la orienta sola. Su atributo
# uValue va de 0 (principio de la curva) a 1 (final).
mp = cmds.pathAnimation(van_ruta, curve=ruta, fractionMode=True, follow=True, followAxis="z", upAxis="y",
                        worldUpType="vector", worldUpVector=(0, 1, 0), startTimeU=1, endTimeU=F_FIN)
cmds.cutKey(mp, attribute="uValue")  # se quitan sus claves para poner las de cada plano


def u_en_z(z):
    """uValue cuando la furgoneta esta en esa Z del tramo recto."""
    return (Z_INICIO - z) / LONGITUD


LONGITUD_RECTA = Z_INICIO - z_giro
LONGITUD_ARCO = math.pi * RADIO_GIRO / 2.0
U_FIN_GIRO = (LONGITUD_RECTA + LONGITUD_ARCO) / LONGITUD
U_PARADA = (LONGITUD_RECTA + LONGITUD_ARCO + (PARADA_X - centro_x)) / LONGITUD

(_, a0, a1), (_, b0, b1), (_, c0, c1), (_, d0, d1), (_, e0, e1) = PLANOS
for fotograma, u in ((a0, u_en_z(TRAMO_A[0])), (a1, u_en_z(TRAMO_A[1])),
                     (b0, u_en_z(TRAMO_B[0])), (b1, u_en_z(TRAMO_B[1])),
                     (c0, u_en_z(TRAMO_C[0])), (c1, u_en_z(TRAMO_C[1])),
                     (d0, u_en_z(Z_INICIO_GIRO_PLANO_D)), (d1, U_FIN_GIRO),
                     (e0, U_FIN_GIRO), (F_PARADA, U_PARADA), (e1, U_PARADA)):
    clave(mp, "uValue", fotograma, u)
# Velocidad constante dentro de cada plano; al final frena hasta pararse.
cmds.keyTangent(mp, attribute="uValue", inTangentType="linear", outTangentType="linear")
cmds.keyTangent(mp, attribute="uValue", time=(F_PARADA, F_PARADA), inTangentType="flat", outTangentType="flat")

# Ruedas: giran segun la distancia recorrida, asi nunca patinan.
for rueda in ("FUR:rueda_FR", "FUR:rueda_FL", "FUR:rueda_RL", "FUR:rueda_RR"):
    cmds.expression(name="EXP_giro_" + rueda.split(":")[-1],
                    string="%s.rotateY = -(%s.uValue * %f / %f) * 57.29578;" % (rueda, mp, LONGITUD, RADIO_RUEDA))

# Frenazo: el morro se hunde y rebota, y la cola derrapa un poco.
for fotograma, grados in ((F_PARADA - 12, 0), (F_PARADA - 3, 5), (F_PARADA + 4, -1.5), (F_PARADA + 10, 0)):
    clave(van_frenada, "rotateX", fotograma, grados)
for fotograma, grados in ((F_PARADA - 12, 0), (F_PARADA, -14)):
    clave(van_frenada, "rotateY", fotograma, grados)

# =============================================================================
# 4. LAS CAMARAS, una por plano
# =============================================================================
# A: sujeta a la furgoneta, de lado. Empieza con el logo llenando la pantalla
# (enlaza con el final de la escena 1) y se aleja hasta verla entera.
cam_a = crear_camara("CAM_A_logo")
cmds.parent(cam_a, van_ruta, relative=True)
cmds.setAttr(cam_a + ".rotateY", 90)
lateral = ANCHO / 2.0
for fotograma, (x, y, z) in ((a0, (lateral + 195, LOGO_ALTO, LOGO_LARGO)), (a1, (lateral + 680, 115, 0))):
    for canal, valor in zip(("translateX", "translateY", "translateZ"), (x, y, z)):
        clave(cam_a, canal, fotograma, valor)
cmds.keyTangent(cam_a, inTangentType="flat", outTangentType="flat")
# El relleno de la furgoneta solo hace falta en este plano; visto desde arriba
# dejaba una mancha blanca en el suelo, asi que se apaga al cortar.
clave(relleno_van, "intensity", a0, 320.0)
clave(relleno_van, "intensity", a1 + 1, 0.0)
cmds.keyTangent(relleno_van, attribute="intensity", outTangentType="step")

# B: fija al borde del bosque, girando para seguir a la furgoneta al pasar.
cam_b = crear_camara("CAM_B_lateral")
cmds.move(-3885, 90, (TRAMO_B[0] + TRAMO_B[1]) / 2.0, cam_b)
objetivo_b = cmds.spaceLocator(name="OBJETIVO_camara_B")[0]
cmds.parent(objetivo_b, van_ruta, relative=True)
cmds.move(0, 100, 0, objetivo_b, localSpace=True)
cmds.aimConstraint(objetivo_b, cam_b, aimVector=(0, 0, -1), upVector=(0, 1, 0), worldUpType="vector",
                   worldUpVector=(0, 1, 0))

# C: aerea sobre la carretera, mirando a lo largo de ella (desde el bosque las
# copas de los arboles la tapaban).
cam_c = crear_camara("CAM_C_aerea", focal=28)
cmds.move(-3450, 1100, 3500, cam_c)
apuntar(cam_c, (-2985, SUELO_Y, 1700))

# D y E: cenitales. Con este giro la casa queda arriba en pantalla y la
# furgoneta entra por la derecha, como en el storyboard.
cam_d = crear_camara("CAM_D_giro", focal=28)
cmds.move(-2500, 2200, 350, cam_d)
cmds.rotate(-90, -90, 0, cam_d)
cam_e = crear_camara("CAM_E_frenazo", focal=28)
cmds.move(-2450, 1300, 120, cam_e)
cmds.rotate(-90, -90, 0, cam_e)

# Desde arriba el suelo recibe la luz de lleno y parecia de dia. Igual que en
# un rodaje, se ilumina distinto por plano: en los cenitales se bajan la luna y
# los faros (el cambio coincide con el corte, asi que no se nota).
for luz_nodo, normal, cenital in [(l, 0.4, 0.17) for l in cmds.ls(type="directionalLight", long=True)] + \
                                 [(cmds.listRelatives(f, shapes=True, fullPath=True)[0], 600.0, 130.0) for f in faros]:
    clave(luz_nodo, "intensity", a0, normal)
    clave(luz_nodo, "intensity", d0, cenital)
    cmds.keyTangent(luz_nodo, attribute="intensity", outTangentType="step")

camaras = [cam_a, cam_b, cam_c, cam_d, cam_e]
cmds.group([cam_b, cam_c, cam_d, cam_e, ruta, cielo, cmds.listRelatives(ambiente, parent=True)[0]],
           name="GRP_animacion_escena2")

# Camera Sequencer: guarda que camara toca en cada tramo, para sacar un solo
# playblast con los cortes ya hechos (Playblast > Playblast Sequence).
try:
    for (nombre, inicio, fin), cam in zip(PLANOS, camaras):
        cmds.shot("PLANO_" + nombre, startTime=inicio, endTime=fin, sequenceStartTime=inicio,
                  sequenceEndTime=fin, currentCamera=cam)
except Exception as error:
    print("No se pudo crear la secuencia de planos: %s" % error)

# =============================================================================
# 5. AJUSTES DE TIEMPO E IMAGEN
# =============================================================================
cmds.currentUnit(time="film")  # "film" = 24 fotogramas por segundo
cmds.playbackOptions(minTime=1, maxTime=F_FIN, animationStartTime=1, animationEndTime=F_FIN)
cmds.setAttr("defaultResolution.width", 1920)
cmds.setAttr("defaultResolution.height", 1080)
cmds.setAttr("defaultResolution.deviceAspectRatio", 1920.0 / 1080.0)
cmds.setAttr("defaultRenderGlobals.startFrame", 1)
cmds.setAttr("defaultRenderGlobals.endFrame", F_FIN)
cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)  # bordes suavizados
cmds.setAttr("perspShape.renderable", 0)
cmds.setAttr(cmds.listRelatives(cam_a, shapes=True)[0] + ".renderable", 1)

# =============================================================================
# 6. GUARDAR
# =============================================================================
cmds.currentTime(1)
cmds.select(clear=True)
if not os.path.isdir(os.path.dirname(SALIDA)):
    os.makedirs(os.path.dirname(SALIDA))
cmds.file(rename=SALIDA)
cmds.file(save=True, type="mayaBinary")
print("Escena guardada en " + SALIDA)

if _SIN_VENTANA:
    # Arnold falla al cerrar Maya sin ventana; se sale directamente, ya esta guardado.
    sys.stdout.flush()
    os._exit(0)
else:
    # Dentro de Maya: mirar por la primera camara con luces y texturas activas.
    for panel in cmds.getPanel(type="modelPanel"):
        if cmds.modelPanel(panel, query=True, camera=True).startswith("persp"):
            cmds.lookThru(panel, cam_a)
            cmds.modelEditor(panel, edit=True, displayAppearance="smoothShaded",
                             displayTextures=True, displayLights="all")
