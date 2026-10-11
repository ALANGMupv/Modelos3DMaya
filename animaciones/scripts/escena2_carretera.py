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
import random
import sys

import maya.cmds as cmds

# Con mayapy (Maya sin ventana) hay que arrancar el motor a mano.
_SIN_VENTANA = not hasattr(cmds, "polyCube")
if _SIN_VENTANA:
    import maya.standalone
    maya.standalone.initialize(name="python")

import maya.api.OpenMaya as om

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
PLANOS = [("A_logo", 1, 96), ("B_lateral", 97, 167), ("C_aerea", 168, 251),
          ("D_giro", 252, 323), ("E_frenazo", 324, 377)]
F_FIN = PLANOS[-1][2]
F_PARADA = 353             # fotograma en que la furgoneta queda parada

# Tramo de carretera (Z de salida, Z de llegada) que recorre en los planos A, B y C.
# Como hay corte entre planos, en cada uno se coloca donde mejor se ve.
TRAMO_A = (5900.0, 2800.0)
TRAMO_B = (3300.0, 1700.0)
# Fotogramas que tarda en recorrer el tramo B entero. El plano B corta antes de
# que lo acabe; asi la velocidad no cambia aunque se acorte o alargue el plano.
FOTOGRAMAS_TRAMO_B = 83
TRAMO_C = (2700.0, 800.0)
Z_INICIO_GIRO_PLANO_D = 1200.0

# Centro del logo en el lateral, medido desde el centro de la furgoneta a ras
# de suelo: (altura, posicion a lo largo; negativo = hacia atras).
LOGO_ALTO, LOGO_LARGO = 126.0, -95.0

# Cielo y luna.
TEXTURA_CIELO = ANIMACIONES + "/texturas/cielo_noche.jpg"
CIELO_BRILLO = 1.0         # 1 = la foto tal cual; menos = mas oscuro
CIELO_GIRO = 0.0           # grados; gira el cielo si la costura de la foto entra en plano
LUNA_ELEVACION = 10.0      # grados sobre el horizonte
LUNA_AZIMUT = 0.0          # 0 = al este, justo detras de la furgoneta vista de lado
LUNA_DISTANCIA = 40000.0
LUNA_RADIO = 1000.0

# Optimizacion.
MARGEN_ENCUADRE = 1.2      # cuanto mas alla del encuadre se conserva vegetacion
DISTANCIA_DETALLE = 2600.0 # mas lejos de la camara que esto, un arbol se cambia por su version ligera
REDUCCION_ARBOLES = 50     # % de caras que se quitan en la version ligera de pino y roble
COPA_DESDE = 0.5           # los arbustos usan las piezas del arbol por encima de esta fraccion de su altura
REDUCCION_HORIZONTE = 75   # % de caras que se quitan a los arboles del horizonte y del telon
ARBOLES_FRANJA_MEDIA = 45  # arboles ligeros entre la cuneta y el horizonte
ARBOLES_HORIZONTE = 120    # arboles muy ligeros que forman el bosque del horizonte
ARBOLES_TELON = 40         # arboles gigantes en el borde del mapa que cierran el fondo
ARBOLES_JUNTO_CASA = 30    # arboles ligeros repartidos a izquierda y derecha de la casa
ARBUSTOS = 90              # arbustos (copas de arbol apoyadas en el suelo)
NIEBLA_DENSIDAD = 0.3      # 0 = sin niebla baja; 0.5 = muy espesa
SEMILLA = 7                # cambia el numero para otro reparto de pinos


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

# Cielo nocturno: una esfera enorme que envuelve todo, con una foto de cielo
# estrellado por dentro. "surfaceShader" es un material que no reacciona a las
# luces: muestra la imagen tal cual, que es lo que se quiere para un fondo.
cielo = cmds.polySphere(name="CIELO_noche", radius=45000, subdivisionsX=32, subdivisionsY=16)[0]
cmds.move(-1000, 0, 1000, cielo)
cmds.rotate(0, CIELO_GIRO, 0, cielo)
# La foto es una franja panoramica: se ajusta para que ocupe solo la parte baja
# del cielo (del horizonte a unos 40 grados), que es la que ven las camaras.
# Mas arriba se repite, pero ningun plano mira tan alto.
cmds.polyEditUV(cielo + ".map[*]", pivotU=0, pivotV=0.47, scaleU=1, scaleV=1 / 0.22)
mat_cielo = cmds.shadingNode("surfaceShader", asShader=True, name="MAT_cielo_noche")
if os.path.isfile(TEXTURA_CIELO):
    tex_cielo = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name="TEX_cielo_noche")
    cmds.setAttr(tex_cielo + ".fileTextureName", TEXTURA_CIELO, type="string")
    cmds.setAttr(tex_cielo + ".colorGain", CIELO_BRILLO, CIELO_BRILLO, CIELO_BRILLO, type="double3")
    cmds.connectAttr(tex_cielo + ".outColor", mat_cielo + ".outColor")
else:
    cmds.setAttr(mat_cielo + ".outColor", 0.012, 0.022, 0.06, type="double3")
sg_cielo = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="MAT_cielo_nocheSG")
cmds.connectAttr(mat_cielo + ".outColor", sg_cielo + ".surfaceShader")
cmds.sets(cielo, edit=True, forceElement=sg_cielo)

# Luna: una esfera que brilla sola y, detras, un plano con un degradado
# circular transparente que hace de halo.
elevacion, azimut = math.radians(LUNA_ELEVACION), math.radians(LUNA_AZIMUT)
luna_pos = (-3500 + LUNA_DISTANCIA * math.cos(elevacion) * math.cos(azimut),
            LUNA_DISTANCIA * math.sin(elevacion),
            3500 + LUNA_DISTANCIA * math.cos(elevacion) * math.sin(azimut))
luna_geo = cmds.polySphere(name="LUNA", radius=LUNA_RADIO, subdivisionsX=24, subdivisionsY=12)[0]
cmds.move(luna_pos[0], luna_pos[1], luna_pos[2], luna_geo)
mat_luna = cmds.shadingNode("surfaceShader", asShader=True, name="MAT_luna")
cmds.setAttr(mat_luna + ".outColor", 0.95, 0.95, 0.84, type="double3")
sg_luna = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="MAT_lunaSG")
cmds.connectAttr(mat_luna + ".outColor", sg_luna + ".surfaceShader")
cmds.sets(luna_geo, edit=True, forceElement=sg_luna)

halo = cmds.polyPlane(name="LUNA_halo", width=LUNA_RADIO * 8, height=LUNA_RADIO * 8, axis=(-1, 0, 0),
                      subdivisionsX=1, subdivisionsY=1)[0]
cmds.move(luna_pos[0] + LUNA_RADIO * 1.5, luna_pos[1], luna_pos[2], halo)
degradado = cmds.shadingNode("ramp", asTexture=True, name="RAMPA_halo_luna")
cmds.setAttr(degradado + ".type", 4)  # 4 = circular: el valor cambia del centro hacia fuera
for i, (posicion, transparencia) in enumerate(((0.0, 0.55), (0.55, 1.0), (1.0, 1.0))):
    cmds.setAttr("%s.colorEntryList[%d].position" % (degradado, i), posicion)
    cmds.setAttr("%s.colorEntryList[%d].color" % (degradado, i), transparencia, transparencia, transparencia,
                 type="double3")
mat_halo = cmds.shadingNode("surfaceShader", asShader=True, name="MAT_halo_luna")
cmds.setAttr(mat_halo + ".outColor", 0.5, 0.62, 1.0, type="double3")
cmds.connectAttr(degradado + ".outColor", mat_halo + ".outTransparency")
sg_halo = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="MAT_halo_lunaSG")
cmds.connectAttr(mat_halo + ".outColor", sg_halo + ".surfaceShader")
cmds.sets(halo, edit=True, forceElement=sg_halo)

for geo in (cielo, luna_geo, halo):
    forma = cmds.listRelatives(geo, shapes=True)[0]
    cmds.setAttr(forma + ".castsShadows", 0)
    cmds.setAttr(forma + ".receiveShadows", 0)

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
# Donde va la furgoneta cuando corta el plano B, a la velocidad del tramo entero.
Z_CORTE_B = TRAMO_B[0] + (TRAMO_B[1] - TRAMO_B[0]) * min(1.0, (b1 - b0) / float(FOTOGRAMAS_TRAMO_B))
for fotograma, u in ((a0, u_en_z(TRAMO_A[0])), (a1, u_en_z(TRAMO_A[1])),
                     (b0, u_en_z(TRAMO_B[0])), (b1, u_en_z(Z_CORTE_B)),
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
cmds.group([cam_b, cam_c, cam_d, cam_e, ruta, cielo, luna_geo, halo, cmds.listRelatives(ambiente, parent=True)[0]],
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
# 5. OPTIMIZACION: ocultar lo que ninguna camara ve
# El entorno es una referencia, asi que no se borra nada: se oculta desde esta
# escena. Lo oculto no se dibuja en el visor ni se renderiza.
# =============================================================================
def hijos(nodo):
    return cmds.listRelatives(nodo, children=True, type="transform", fullPath=True) or []


def caras_dibujadas(raices):
    """Suma las caras de todas las mallas visibles bajo 'raices', contando
    cada copia instanciada (que es lo que de verdad se dibuja)."""
    visibles = {}

    def visible(ruta):
        if ruta not in visibles:
            padre = ruta.rsplit("|", 1)[0]
            visibles[ruta] = bool(cmds.getAttr(ruta + ".visibility")) and (not padre or visible(padre))
        return visibles[ruta]

    total = 0
    for forma in cmds.ls(raices, dag=True, type="mesh", noIntermediate=True, long=True, allPaths=True):
        if visible(forma):
            total += cmds.polyEvaluate(forma, face=True)
    return total


RAICES_CASA = ["ENT:CASA", "ENT:TECHOS_INTERIORES"]
RAICES_VEGETACION = ["ENT:Arboles_y_Vegetacion"]
caras_casa_antes = caras_dibujadas(RAICES_CASA)
caras_vegetacion_antes = caras_dibujadas(RAICES_VEGETACION)

# --- Casa: desde fuera solo se ve el cascaron. Se conservan muros, puertas,
# ventanas y postes; muebles, suelos, lamparas y techos interiores se ocultan.
CONSERVAR_EN_CASA = ("Wall", "Door", "Window", "Post")
QUITAR_EN_CASA = ("Lamp", "Light")  # los apliques se llaman WallLamp/WallLight y son de interior
for forma in cmds.ls("ENT:CASA", dag=True, type="mesh", noIntermediate=True, long=True, allPaths=True):
    dentro_de_casa = forma.split("|ENT:CASA|", 1)[-1]
    if (not any(clave_nombre in dentro_de_casa for clave_nombre in CONSERVAR_EN_CASA)
            or any(clave_nombre in dentro_de_casa for clave_nombre in QUITAR_EN_CASA)):
        cmds.setAttr(cmds.listRelatives(forma, parent=True, fullPath=True)[0] + ".visibility", 0)
cmds.setAttr("ENT:TECHOS_INTERIORES.visibility", 0)

# --- Vegetacion: se mira, plano a plano y cada pocos fotogramas, que arboles,
# arbustos y hierbas caen dentro del encuadre de alguna camara y a que
# distancia minima. Con eso cada planta acaba en uno de tres casos:
#   - nunca entra en plano          -> se oculta
#   - entra en plano, pero de lejos -> un arbol se cambia por un pino sencillo;
#                                      arbustos y hierbas se ocultan (no se aprecian)
#   - entra en plano de cerca       -> se deja el modelo real
candidatos = []
for grupo in ("ENT:Arboles_Instanciados", "ENT:Bosque_Perimetral_Instanciado", "ENT:Arbustos_Instanciados",
              "ENT:Hierbas_Instanciadas"):
    candidatos += hijos(grupo)
for grupo in ("ENT:Vegetacion_Prolongacion", "ENT:Vegetacion_Tramo_Entrada"):
    for subgrupo in hijos(grupo):
        candidatos += hijos(subgrupo)

datos = []  # (ruta, centro, radio, altura) de cada planta
for planta in candidatos:
    x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(planta)
    datos.append((planta, ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0),
                  max(x1 - x0, y1 - y0, z1 - z0) / 2.0, y1 - y0))

distancia_minima = {}  # indice de la planta -> lo mas cerca que llega a estar de una camara
for (nombre, inicio, fin), cam in zip(PLANOS, camaras):
    forma_cam = cmds.listRelatives(cam, shapes=True)[0]
    focal = cmds.getAttr(forma_cam + ".focalLength")
    # Tangente de medio angulo de vision, en horizontal y en vertical.
    tan_h = cmds.getAttr(forma_cam + ".horizontalFilmAperture") * 25.4 / 2.0 / focal * MARGEN_ENCUADRE
    tan_v = cmds.getAttr(forma_cam + ".verticalFilmAperture") * 25.4 / 2.0 / focal * MARGEN_ENCUADRE
    for fotograma in range(inicio, fin + 1, 4):
        cmds.currentTime(fotograma)
        a_camara = om.MMatrix(cmds.xform(cam, query=True, worldSpace=True, matrix=True)).inverse()
        for i, (planta, centro_planta, radio, _) in enumerate(datos):
            p = om.MPoint(centro_planta) * a_camara  # la planta vista desde la camara
            profundidad = -p.z                       # la camara mira hacia su -Z
            if profundidad < -radio:
                continue
            profundidad = max(profundidad, 1.0)
            if abs(p.x) <= profundidad * tan_h + radio and abs(p.y) <= profundidad * tan_v + radio:
                distancia_minima[i] = min(distancia_minima.get(i, profundidad), profundidad)

# --- Versiones ligeras de los arboles del propio entorno. Se copia cada
# prototipo (pino, roble, arbol desnudo), se funde en una sola malla y se le
# quita parte de las caras. Es el mismo modelo, solo que mas barato de dibujar.
def copia_ligera(prototipo, nombre, reduccion, solo_copa=False):
    copia = cmds.duplicate(prototipo, name=nombre + "_tmp")[0]
    if cmds.listRelatives(copia, parent=True):
        copia = cmds.parent(copia, world=True)[0]
    piezas = [cmds.listRelatives(m, parent=True, fullPath=True)[0]
              for m in cmds.listRelatives(copia, allDescendents=True, type="mesh", fullPath=True)
              if not cmds.getAttr(m + ".intermediateObject")]
    if solo_copa:
        # Para los arbustos: solo las piezas de la mitad de arriba del arbol.
        alto = cmds.exactWorldBoundingBox(copia)[4]
        sobran = [p for p in piezas if cmds.exactWorldBoundingBox(p)[1] < alto * COPA_DESDE]
        piezas = [p for p in piezas if p not in sobran]
        cmds.delete(sobran)
    malla = cmds.polyUnite(piezas, name=nombre, constructionHistory=False)[0]
    if cmds.objExists(copia):
        cmds.delete(copia)
    if reduccion > 0:
        cmds.polyReduce(malla, percentage=reduccion, keepQuadsWeight=0, constructionHistory=False)
    if solo_copa:
        # La copa se baja hasta apoyarla en el suelo y se centra.
        x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(malla)
        cmds.move(-(x0 + x1) / 2.0, -y0, -(z0 + z1) / 2.0, malla, relative=True)
        cmds.makeIdentity(malla, apply=True, translate=True)
    cmds.setAttr(malla + ".visibility", 0)  # el molde no se ve; se ven sus copias
    return malla


ligeros = {
    "Pino": copia_ligera("ENT:Prototipo_Arbol_Pino", "ARBOL_ligero_pino", REDUCCION_ARBOLES),
    "Roble": copia_ligera("ENT:Prototipo_Arbol_Roble", "ARBOL_ligero_roble", REDUCCION_ARBOLES),
    "Desnudo": copia_ligera("ENT:Prototipo_Arbol_Desnudo", "ARBOL_ligero_desnudo", 0),
}
arbustos_molde = [copia_ligera("ENT:Prototipo_Arbol_Roble", "ARBUSTO_copa_roble", REDUCCION_ARBOLES, solo_copa=True),
                  copia_ligera("ENT:Prototipo_Arbol_Pino", "ARBUSTO_copa_pino", REDUCCION_ARBOLES, solo_copa=True)]

random.seed(SEMILLA)
anadidos = []


def plantar(molde, nombre):
    """Copia instanciada de un molde. Una instancia no duplica la malla: Maya
    la guarda una vez y la dibuja en cada sitio."""
    copia = cmds.instance(molde, name="%s_%03d" % (nombre, len(anadidos)))[0]
    cmds.setAttr(copia + ".visibility", 1)
    anadidos.append(copia)
    return copia


def tipo_de_arbol(nombre):
    for tipo in ligeros:
        if tipo in nombre:
            return tipo
    return random.choice(("Pino", "Pino", "Roble"))


reales = sustituidos = 0
ocupado = []  # posiciones (x, z) donde ya hay un arbol
for i, (planta, centro_planta, radio, altura) in enumerate(datos):
    if i not in distancia_minima:
        cmds.setAttr(planta + ".visibility", 0)        # nunca entra en plano
    elif distancia_minima[i] <= DISTANCIA_DETALLE:
        reales += 1                                    # se ve de cerca: modelo real intacto
        if altura > 300:
            ocupado.append((centro_planta[0], centro_planta[2]))
    else:
        cmds.setAttr(planta + ".visibility", 0)        # se ve de lejos
        if altura > 300:                               # es un arbol: su version ligera, en el mismo sitio
            copia = plantar(ligeros[tipo_de_arbol(planta.split("|")[-1])], "ARBOL_lejano")
            cmds.xform(copia, worldSpace=True, matrix=cmds.xform(planta, query=True, worldSpace=True, matrix=True))
            ocupado.append((centro_planta[0], centro_planta[2]))
            sustituidos += 1


def repartir(cantidad, zonas, moldes, nombre, separacion, tamano):
    """Reparte copias al azar dentro de unas zonas rectangulares (x0, x1, z0, z1)
    sin que queden pegadas a otro arbol."""
    hechos = intentos = 0
    areas = [(x1 - x0) * (z1 - z0) for x0, x1, z0, z1 in zonas]  # las zonas grandes reciben mas
    while hechos < cantidad and intentos < cantidad * 60:
        intentos += 1
        x0, x1, z0, z1 = random.choices(zonas, weights=areas)[0]
        x, z = random.uniform(x0, x1), random.uniform(z0, z1)
        if any(abs(x - ox) < separacion and abs(z - oz) < separacion for ox, oz in ocupado):
            continue
        copia = plantar(random.choice(moldes), nombre)
        escala = random.uniform(tamano[0], tamano[1])
        cmds.move(x, SUELO_Y - 2, z, copia)
        cmds.rotate(0, random.uniform(0, 360), 0, copia)
        cmds.scale(escala, escala * random.uniform(0.9, 1.1), escala, copia)
        ocupado.append((x, z))
        hechos += 1
    return hechos


arboles_mezcla = [ligeros["Pino"], ligeros["Pino"], ligeros["Roble"], ligeros["Roble"], ligeros["Desnudo"]]
# Para lo que queda muy lejos, una version todavia mas ligera de los mismos arboles.
muy_ligeros = [copia_ligera("ENT:Prototipo_Arbol_Pino", "ARBOL_muy_ligero_pino", REDUCCION_HORIZONTE),
               copia_ligera("ENT:Prototipo_Arbol_Roble", "ARBOL_muy_ligero_roble", REDUCCION_HORIZONTE)]
mezcla_lejana = muy_ligeros + muy_ligeros + [ligeros["Desnudo"]]

# El bosque se rellena por capas, pensando en lo que ven las camaras laterales
# (miran al este): cada capa esta mas lejos que la anterior, y eso es lo que da
# sensacion de profundidad.
#   1. Franja media: entre los arboles reales de la cuneta y el horizonte.
#      Se deja un pasillo sin arboles justo delante de la camara lateral (B),
#      para que por ese hueco se siga viendo la luna sobre el bosque lejano.
z_pasillo = (TRAMO_B[0] + TRAMO_B[1]) / 2.0
n_media = repartir(ARBOLES_FRANJA_MEDIA,
                   [(-2100, 450, 1250, z_pasillo - 500), (-2100, 450, z_pasillo + 500, 6900),
                    (-2650, -2100, 1250, z_pasillo - 500), (-2650, -2100, z_pasillo + 500, 3300)],
                   arboles_mezcla, "ARBOL_medio", 300, (0.85, 1.25))
#   2. Horizonte: muchos arboles muy ligeros, lejos.
n_horizonte = repartir(ARBOLES_HORIZONTE, [(500, 3300, 900, z_pasillo - 700), (500, 3300, z_pasillo + 700, 6900)],
                       mezcla_lejana, "ARBOL_horizonte", 250, (0.9, 1.4))
#   3. Telon: una fila de arboles el doble de grandes en el borde del terreno.
#      Truco de perspectiva: a esa distancia parecen de tamano normal, pero
#      cierran el fondo para que nunca se vea donde acaba el mapa.
n_telon = repartir(ARBOLES_TELON, [(3300, 3560, 600, z_pasillo - 700), (3300, 3560, z_pasillo + 700, 7000)],
                   mezcla_lejana, "ARBOL_telon", 170, (1.7, 2.3))
#      En el pasillo de la luna el telon es bajo: tapa el horizonte sin tapar la luna.
n_telon += repartir(8, [(3300, 3560, z_pasillo - 700, z_pasillo + 700)], mezcla_lejana, "ARBOL_telon_bajo", 150,
                    (0.6, 0.8))

# A izquierda y derecha de la casa: junto a la parcela y junto al edificio,
# dejando libres el camino de grava y la zona donde gira la furgoneta.
ZONAS_CASA = [(-2620, -2120, -1150, -480), (-2620, -2120, 480, 1150),
              (-2000, -500, -1750, -1230), (-2000, -500, 1340, 1850)]
n_casa = repartir(ARBOLES_JUNTO_CASA, ZONAS_CASA, arboles_mezcla, "ARBOL_casa", 270, (0.8, 1.15))
# Arbustos: copas de los mismos arboles, apoyadas en el suelo y en pequeno.
# Junto a la casa y tambien a lo largo de la cuneta, detras de la furgoneta.
ZONAS_ARBUSTOS = [(-2640, -2095, -1150, -330), (-2640, -2095, 330, 1150),
                  (-2050, -500, -1500, -1150), (-2050, -500, 1260, 1600),
                  (-2680, -2430, 1300, 6500), (-2680, -2430, 1300, 6500)]
n_arbustos = repartir(ARBUSTOS, ZONAS_ARBUSTOS, arbustos_molde, "ARBUSTO", 150, (0.3, 0.5))
grp_anadidos = cmds.group(list(ligeros.values()) + muy_ligeros + arbustos_molde + anadidos,
                          name="GRP_vegetacion_anadida")

# Niebla baja: laminas verticales casi transparentes entre las capas de arboles,
# opacas a ras de suelo y transparentes arriba. Cada capa de bosque queda un
# poco mas velada que la anterior, que es como el ojo lee la distancia de noche.
# Solo en los planos laterales (A y B): vistas desde arriba se notarian.
degradado_niebla = cmds.shadingNode("ramp", asTexture=True, name="RAMPA_niebla")
cmds.setAttr(degradado_niebla + ".type", 0)  # 0 = degradado en vertical
for i, (posicion, transparencia) in enumerate(((0.0, 1.0 - NIEBLA_DENSIDAD), (0.6, 0.93), (1.0, 1.0))):
    cmds.setAttr("%s.colorEntryList[%d].position" % (degradado_niebla, i), posicion)
    cmds.setAttr("%s.colorEntryList[%d].color" % (degradado_niebla, i), transparencia, transparencia, transparencia,
                 type="double3")
mat_niebla = cmds.shadingNode("surfaceShader", asShader=True, name="MAT_niebla")
cmds.setAttr(mat_niebla + ".outColor", 0.16, 0.22, 0.38, type="double3")
cmds.connectAttr(degradado_niebla + ".outColor", mat_niebla + ".outTransparency")
sg_niebla = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="MAT_nieblaSG")
cmds.connectAttr(mat_niebla + ".outColor", sg_niebla + ".surfaceShader")
laminas = []
for x_lamina in (-2380, -1500, -400, 900, 2300):
    lamina = cmds.polyPlane(name="NIEBLA_lamina_%d" % len(laminas), width=7400, height=1000, axis=(-1, 0, 0),
                            subdivisionsX=1, subdivisionsY=1)[0]
    cmds.move(x_lamina, SUELO_Y + 500, 3700, lamina)
    cmds.sets(lamina, edit=True, forceElement=sg_niebla)
    forma_lamina = cmds.listRelatives(lamina, shapes=True)[0]
    cmds.setAttr(forma_lamina + ".castsShadows", 0)
    cmds.setAttr(forma_lamina + ".receiveShadows", 0)
    laminas.append(lamina)
grp_niebla = cmds.group(laminas, name="GRP_niebla")
clave(grp_niebla, "visibility", a0, 1)
clave(grp_niebla, "visibility", c0, 0)

print("OPTIMIZACION - caras que se dibujan (antes -> despues)")
print("  Casa:        %7d -> %7d" % (caras_casa_antes, caras_dibujadas(RAICES_CASA)))
print("  Vegetacion:  %7d -> %7d  (%d de %d plantas se quedan con su modelo real)" % (
    caras_vegetacion_antes, caras_dibujadas(RAICES_VEGETACION), reales, len(datos)))
print("  Anadido:           0 -> %7d  (%d arboles lejanos en version ligera, %d franja media, %d horizonte, "
      "%d telon, %d junto a la casa, %d arbustos)" % (caras_dibujadas([grp_anadidos]), sustituidos, n_media,
                                                      n_horizonte, n_telon, n_casa, n_arbustos))
print("  Caras de cada molde: " + ", ".join(
    "%s %d" % (m, cmds.polyEvaluate(m, face=True)) for m in list(ligeros.values()) + muy_ligeros + arbustos_molde))

# =============================================================================
# 6. AJUSTES DE TIEMPO E IMAGEN
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
# 7. GUARDAR
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
