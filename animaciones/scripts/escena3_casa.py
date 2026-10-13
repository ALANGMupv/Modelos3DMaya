# -*- coding: utf-8 -*-
"""
PickABoo - Trailer - ESCENA 3: la puerta, el fantasma y el titulo.

La camara se acerca a la casa, las puertas se abren solas, un fantasma cruza
flotando, se gira, se asusta al ver al jugador, huye, y las puertas se cierran
de golpe mostrando el logo.

Usa el mismo entorno que la escena 2 (enlazado como referencia, sin tocarlo),
la furgoneta aparcada y el fantasma de Modelos/Fantasma. Guarda
animaciones/escenas/escena3_casa.mb

Como ejecutarlo dentro de Maya:
    Windows > General Editors > Script Editor, pestana Python, y pegar:
        exec(open(r"C:/Users/Alejandro/Desktop/Modelos3DMaya/animaciones/scripts/escena3_casa.py", encoding="utf-8").read())

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
# AJUSTES. Unidades en centimetros, en las coordenadas del entorno: la fachada
# de la casa mira al oeste (-X), la puerta esta en X=-2060 y el suelo del
# recibidor en Y=-49. Visto desde fuera, +Z queda a la derecha.
# =============================================================================
try:
    ANIMACIONES = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
except NameError:
    ANIMACIONES = "C:/Users/Alejandro/Desktop/Modelos3DMaya/animaciones"
REPO = os.path.dirname(ANIMACIONES)
ENTORNO = REPO + "/Entornos/entornoCarreteraConCasa_EntradaLarga.mb"
FURGONETA = REPO + "/Modelos/Furgoneta/boorgoneta_final.mb"
TEXTURAS_FURGONETA = REPO + "/Modelos/Furgoneta/sourceimages"
# Se usa el FBX del fantasma porque trae cuerpo, ojos, cejas y boca como piezas
# sueltas; en el .mb estan fundidas en una sola malla y no se pueden animar.
FANTASMA = REPO + "/Modelos/Fantasma/fantasma.fbx"
# Si algun dia se exporta la textura del cuerpo desde Substance Painter, guardala
# con este nombre y el script la usara en vez del color liso.
TEXTURA_FANTASMA = REPO + "/Modelos/Fantasma/sourceimages/fantasma_BaseColor.png"
LOGO = REPO + "/Entornos/EntornoTelefono/sourceimages/Logo_Pick_A_Boo_Nuevo_Transparente.png"
TEXTURA_CIELO = ANIMACIONES + "/texturas/cielo_noche.jpg"
SALIDA = ANIMACIONES + "/escenas/escena3_casa.mb"

# Planos: (nombre, primer fotograma, ultimo fotograma).
PLANOS = [("A_fachada", 1, 96), ("B_puertas", 97, 168), ("C_fantasma", 169, 264), ("D_susto", 265, 312),
          ("E_huida", 313, 348), ("F_retirada", 349, 408), ("G_titulo", 409, 456)]
F_FIN = PLANOS[-1][2]

# La puerta.
PUERTA_X, PUERTA_Z = -2060.0, 21.0   # centro del hueco
SUELO_CASA = -49.0
ANGULO_ABIERTA = 100.0               # grados que gira cada hoja al abrirse
F_PORTAZO = 414                      # fotograma en que las hojas golpean al cerrarse

# El fantasma.
FANTASMA_ALTO = 110.0                # cm
FANTASMA_X = -1845.0                 # a dos metros por dentro de la puerta
FANTASMA_FLOTA = 30.0                # cm sobre el suelo
F_SUSTO = 287                        # fotograma en que se asusta
F_HUIDA = 320                        # fotograma en que sale disparado

# La furgoneta, aparcada. Esta algo mas atras que al final de la escena 2 para
# dejar sitio a la camara entre ella y la casa; con el corte no se nota.
ESCALA_FURGONETA = 200.0
VAN_X, VAN_Z, VAN_DERRAPE = -2760.0, -16.0, -14.0
SUELO_Y = -53.0

# Cielo y luna. La luna va mas alta que en la escena 2 para que asome sobre el
# tejado al mirar la fachada desde abajo.
CIELO_BRILLO = 1.0
LUNA_ELEVACION = 40.0
LUNA_AZIMUT = 3.0
LUNA_DISTANCIA = 40000.0
LUNA_RADIO = 1000.0

MARGEN_ENCUADRE = 1.2      # cuanto mas alla del encuadre se conserva vegetacion
SEMILLA = 3                # cambia el numero para otro parpadeo y otra sacudida

# Arreglo de huecos en el tejado del recibidor (hecho a mano en Maya y pasado
# aqui para que no se pierda al regenerar): pieza -> desplazamiento (x, y, z).
ARREGLO_TEJADO = {
    "ENT:Fronton_Tejado_11_Room_Finsh_A": (6.67307, -6.385502, -5.993594),
    "ENT:Remate_Alero_Tejado_11_Room_Finsh_L": (183.871053, 0.0, 0.0),
    "ENT:Remate_Alero_Tejado_11_Room_Finsh_R": (24.947988, 0.0, 0.0),
}
# Franjas sin techo en el recibidor, entre un plano de techo y el siguiente
# (X de inicio, X de fin). Por ellas se veian las tejas desde dentro.
HUECOS_TECHO = [(-1778.0, -1760.0), (-1078.0, -1060.0)]

# Vegetacion anadida a la izquierda de la casa (lado -Z), con modelos del entorno.
REDUCCION_ARBOLES = 50     # % de caras que se quitan a los arboles anadidos
COPA_DESDE = 0.5           # los arbustos usan las piezas del arbol por encima de esta fraccion de su altura
ARBOLES_MEDIOS = 14        # al costado del recibidor
ARBOLES_FONDO = 22         # mas lejos y mas grandes, cerrando el horizonte
ARBUSTOS = 30
PIEDRAS = 25
HIERBAS = 40


# =============================================================================
# FUNCIONES DE AYUDA
# =============================================================================
def clave(nodo, atributo, fotograma, valor, tangente="auto"):
    """Pone un keyframe. 'tangente' decide como se llega y se sale de el:
    auto = suave, linear = velocidad constante, flat = frena, step = salta."""
    cmds.setKeyframe(nodo, attribute=atributo, time=fotograma, value=valor,
                     inTangentType="linear" if tangente == "step" else tangente, outTangentType=tangente)


def claves(nodo, atributo, lista, tangente="auto"):
    for fotograma, valor in lista:
        clave(nodo, atributo, fotograma, valor, tangente)


def apuntar(camara, objetivo):
    """Gira la camara para que mire al punto 'objetivo' (x, y, z)."""
    px, py, pz = cmds.xform(camara, query=True, worldSpace=True, translation=True)
    dx, dy, dz = objetivo[0] - px, objetivo[1] - py, objetivo[2] - pz
    cmds.setAttr(camara + ".rotateY", math.degrees(math.atan2(-dx, -dz)))
    cmds.setAttr(camara + ".rotateX", math.degrees(math.atan2(dy, math.hypot(dx, dz))))


def crear_camara(nombre, focal=35):
    cam = cmds.camera(focalLength=focal, horizontalFilmAperture=1.417, verticalFilmAperture=0.797,
                      nearClipPlane=5, farClipPlane=100000)[0]
    cam = cmds.rename(cam, nombre)
    cmds.setAttr(cmds.listRelatives(cam, shapes=True)[0] + ".displayResolution", 1)
    return cam


def clave_camara(cam, fotograma, posicion, objetivo, tangente="auto"):
    """Coloca la camara en 'posicion' mirando a 'objetivo' y lo guarda en ese fotograma."""
    cmds.move(posicion[0], posicion[1], posicion[2], cam)
    apuntar(cam, objetivo)
    for canal in ("translateX", "translateY", "translateZ", "rotateX", "rotateY"):
        clave(cam, canal, fotograma, cmds.getAttr(cam + "." + canal), tangente)


def sacudir(cam, inicio, fin, fuerza):
    """Temblor de camara: balanceo al azar que se va apagando."""
    clave(cam, "rotateZ", inicio - 1, 0)
    for fotograma in range(inicio, fin):
        resto = 1.0 - (fotograma - inicio) / float(fin - inicio)
        clave(cam, "rotateZ", fotograma, random.uniform(-fuerza, fuerza) * resto, "linear")
    clave(cam, "rotateZ", fin, 0)


def material_liso(nombre, color, brillo_propio=(0, 0, 0)):
    mat = cmds.shadingNode("lambert", asShader=True, name="MAT_" + nombre)
    cmds.setAttr(mat + ".color", color[0], color[1], color[2], type="double3")
    cmds.setAttr(mat + ".incandescence", brillo_propio[0], brillo_propio[1], brillo_propio[2], type="double3")
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=mat + "SG")
    cmds.connectAttr(mat + ".outColor", sg + ".surfaceShader")
    return sg, mat


def sin_sombras(geo):
    forma = cmds.listRelatives(geo, shapes=True)[0]
    cmds.setAttr(forma + ".castsShadows", 0)
    cmds.setAttr(forma + ".receiveShadows", 0)


random.seed(SEMILLA)
(_, a0, a1), (_, b0, b1), (_, c0, c1), (_, d0, d1), (_, e0, e1), (_, f0, f1), (_, g0, g1) = PLANOS

# =============================================================================
# 1. ESCENA NUEVA + ENTORNO COMO REFERENCIA (igual que en la escena 2)
# =============================================================================
if cmds.file(query=True, modified=True):
    raise RuntimeError("Tienes cambios sin guardar en Maya. Guarda la escena y vuelve a ejecutar el script.")
cmds.file(new=True, force=True)
cmds.loadPlugin("mtoa", quiet=True)
cmds.loadPlugin("fbxmaya", quiet=True)
cmds.file(ENTORNO, reference=True, namespace="ENT", ignoreVersion=True)

# Luces: se apagan las de dentro de la casa (el visor solo usa 16 a la vez) y la
# cupula de cielo de Arnold, y se reajustan luna y faroles para el visor.
for forma in cmds.ls(lights=True, long=True):
    if "|ENT:CASA|" in forma:
        cmds.setAttr(cmds.listRelatives(forma, parent=True, fullPath=True)[0] + ".visibility", 0)
for cupula in cmds.ls(type="aiSkyDomeLight", long=True):
    cmds.setAttr(cmds.listRelatives(cupula, parent=True, fullPath=True)[0] + ".visibility", 0)
cmds.setAttr("hardwareRenderingGlobals.maxHardwareLights", 16)
for luna_luz in cmds.ls(type="directionalLight", long=True):
    cmds.setAttr(luna_luz + ".intensity", 0.4)
    if "Relleno" in luna_luz:
        cmds.setAttr(luna_luz + ".useDepthMapShadows", 0)
        cmds.setAttr(luna_luz + ".useRayTraceShadows", 0)
for farol in cmds.ls("ENT:Luz_Farol_Maya_*", type="pointLight", long=True):
    cmds.setAttr(farol + ".decayRate", 1)
    cmds.setAttr(farol + ".intensity", 220)
ambiente = cmds.ambientLight(name="LUZ_ambiente_noche", rgb=(0.45, 0.55, 0.9), intensity=0.35)

for pieza_tejado, desplazamiento in ARREGLO_TEJADO.items():
    cmds.setAttr(pieza_tejado + ".translate", desplazamiento[0], desplazamiento[1], desplazamiento[2], type="double3")

# Los huecos del techo se tapan con tiras copiadas del propio techo (mismo
# material), un poco mas anchas que el hueco y 3 mm mas bajas para que, donde
# se solapan con el techo original, no parpadeen.
for i, (x_desde, x_hasta) in enumerate(HUECOS_TECHO):
    tira = cmds.duplicate("ENT:Techo_Plane__1__Room_Finish", name="Techo_tapa_hueco_%d" % i)[0]
    tira = cmds.parent(tira, world=True)[0]
    x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(tira)
    cmds.scale((x_hasta - x_desde + 14) / (x1 - x0), 1, 1, tira, pivot=((x0 + x1) / 2.0, 0, 0), relative=True)
    cmds.move((x_desde + x_hasta) / 2.0 - (x0 + x1) / 2.0, -0.3, 0, tira, relative=True)
# El tejado de la habitacion del fondo asomaba 3 cm por debajo del techo del
# recibidor y se veia por el segundo hueco; se sube un poco.
cmds.move(0, 4, 0, "ENT:Tejado_04_Room_4_x_6", relative=True)

# Cielo: esfera enorme con la foto de cielo estrellado en la mitad de arriba.
cielo = cmds.polySphere(name="CIELO_noche", radius=45000, subdivisionsX=32, subdivisionsY=16)[0]
cmds.move(-1000, 0, 1000, cielo)
cmds.polyEditUV(cielo + ".map[*]", pivotU=0, pivotV=1.0, scaleU=1, scaleV=1.94)
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

# Luna con halo.
elevacion, azimut = math.radians(LUNA_ELEVACION), math.radians(LUNA_AZIMUT)
luna_pos = (PUERTA_X + LUNA_DISTANCIA * math.cos(elevacion) * math.cos(azimut),
            LUNA_DISTANCIA * math.sin(elevacion),
            PUERTA_Z + LUNA_DISTANCIA * math.cos(elevacion) * math.sin(azimut))
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
cmds.rotate(0, 0, -LUNA_ELEVACION, halo)  # de cara a la casa, que la ve desde abajo
degradado = cmds.shadingNode("ramp", asTexture=True, name="RAMPA_halo_luna")
cmds.setAttr(degradado + ".type", 4)
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
    sin_sombras(geo)

# =============================================================================
# 2. LA FURGONETA, aparcada delante de la casa con los faros encendidos
# =============================================================================
nuevos = cmds.file(FURGONETA, i=True, returnNewNodes=True, namespace="FUR", ignoreVersion=True)
curvas_viejas = cmds.ls(nuevos, type="animCurve")
if curvas_viejas:
    cmds.delete(curvas_viejas)
for tex in cmds.ls(nuevos, type="file"):
    local = TEXTURAS_FURGONETA + "/" + os.path.basename(cmds.getAttr(tex + ".fileTextureName"))
    if os.path.isfile(local):
        cmds.setAttr(tex + ".fileTextureName", local, type="string")
x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox("FUR:FURGONETA")
van_escala = cmds.group("FUR:FURGONETA", name="VAN_escala")
cmds.xform(van_escala, pivots=(0, 0, 0), worldSpace=True)
cmds.scale(ESCALA_FURGONETA, ESCALA_FURGONETA, ESCALA_FURGONETA, van_escala)
cmds.move(-(x0 + x1) / 2.0 * ESCALA_FURGONETA, -y0 * ESCALA_FURGONETA, -(z0 + z1) / 2.0 * ESCALA_FURGONETA, van_escala)
LARGO_VAN = (z1 - z0) * ESCALA_FURGONETA
ANCHO_VAN = (x1 - x0) * ESCALA_FURGONETA
faros = []
for lado in (-1, 1):
    foco = cmds.spotLight(name="LUZ_faro_%s" % ("izq" if lado < 0 else "der"), rgb=(1.0, 0.93, 0.75),
                          intensity=420.0, coneAngle=60, penumbra=15)
    foco_t = cmds.listRelatives(foco, parent=True)[0]
    cmds.setAttr(foco + ".decayRate", 1)
    cmds.move(lado * ANCHO_VAN * 0.27, 90, LARGO_VAN / 2.0, foco_t)
    cmds.rotate(-2, 180, 0, foco_t)
    faros.append(foco_t)
van = cmds.group([van_escala] + faros, name="VAN_aparcada")
cmds.xform(van, pivots=(0, 0, 0), worldSpace=True)
cmds.move(VAN_X, SUELO_Y + 4, VAN_Z, van)
cmds.rotate(0, 90 + VAN_DERRAPE, 0, van)  # el morro del modelo mira a +Z; se gira hacia la casa

# =============================================================================
# 3. EL FANTASMA
# Jerarquia de grupos, de fuera a dentro; cada uno se anima para una cosa:
#   GHOST_ruta   -> por donde va y hacia donde mira
#   GHOST_flote  -> el vaiven arriba y abajo, y el salto del susto
#   GHOST_pose   -> estirarse, encogerse e inclinarse
#   GHOST_escala -> agranda el modelo (mide 3 cm) y lo centra
# =============================================================================
nuevos = cmds.file(FANTASMA, i=True, returnNewNodes=True, namespace="GHO")
curvas_viejas = cmds.ls(nuevos, type="animCurve")  # animacion suelta que trae el archivo
if curvas_viejas:
    cmds.delete(curvas_viejas)
sobran = cmds.ls(nuevos, type=("camera", "light"))
piezas =[cmds.listRelatives(m, parent=True, fullPath=True)[0]
          for m in cmds.ls(nuevos, type="mesh", long=True) if not cmds.getAttr(m + ".intermediateObject")]
piezas = [cmds.parent(p, world=True)[0] if cmds.listRelatives(p, parent=True) else p for p in piezas]
for pieza in piezas:
    cmds.delete(pieza, constructionHistory=True)
    cmds.makeIdentity(pieza, apply=True, translate=True, rotate=True, scale=True)
    cmds.xform(pieza, centerPivots=True)

# Se reconoce cada pieza por su numero de caras y por el lado en que esta.
piezas.sort(key=lambda p: cmds.polyEvaluate(p, face=True))
boca, cuerpo = piezas[0], piezas[-1]
resto = piezas[1:-1]
cejas = sorted(resto[:2], key=lambda p: cmds.exactWorldBoundingBox(p)[2])  # [la de -Z, la de +Z]
ojos = sorted(resto[2:], key=lambda p: cmds.exactWorldBoundingBox(p)[2])
boca = cmds.rename(boca, "GHOST_boca")
cuerpo = cmds.rename(cuerpo, "GHOST_cuerpo")
cejas = [cmds.rename(c, "GHOST_ceja_%s" % lado) for c, lado in zip(cejas, ("izq", "der"))]
ojos = [cmds.rename(o, "GHOST_ojo_%s" % lado) for o, lado in zip(ojos, ("izq", "der"))]

# Materiales. El modelo no trae texturas (solo colores lisos, y el cuerpo en
# gris oscuro), asi que aqui se le da aspecto de fantasma: blanco azulado que
# brilla por si mismo.
sg_cuerpo, mat_cuerpo = material_liso("fantasma_cuerpo", (0.74, 0.8, 0.95), (0.13, 0.16, 0.24))
if os.path.isfile(TEXTURA_FANTASMA):
    tex_fantasma = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name="TEX_fantasma")
    cmds.setAttr(tex_fantasma + ".fileTextureName", TEXTURA_FANTASMA, type="string")
    cmds.connectAttr(tex_fantasma + ".outColor", mat_cuerpo + ".color")
sg_negro = material_liso("fantasma_ojos", (0.01, 0.01, 0.015))[0]
sg_boca = material_liso("fantasma_boca", (0.2, 0.015, 0.03))[0]
cmds.sets(cuerpo, edit=True, forceElement=sg_cuerpo)
cmds.sets(ojos + cejas, edit=True, forceElement=sg_negro)
cmds.sets(boca, edit=True, forceElement=sg_boca)

x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(cuerpo)
ESCALA_FANTASMA = FANTASMA_ALTO / (y1 - y0)
ghost_escala = cmds.group([cuerpo, boca] + cejas + ojos, name="GHOST_escala")
cmds.xform(ghost_escala, pivots=(0, 0, 0), worldSpace=True)
cmds.scale(ESCALA_FANTASMA, ESCALA_FANTASMA, ESCALA_FANTASMA, ghost_escala)
cmds.move(-(x0 + x1) / 2.0 * ESCALA_FANTASMA, -y0 * ESCALA_FANTASMA, -(z0 + z1) / 2.0 * ESCALA_FANTASMA, ghost_escala)
if sobran:
    cmds.delete([n for n in sobran if cmds.objExists(n)])
for vacio in cmds.ls("GHO:*", assemblies=True):
    cmds.delete(vacio)

# Luz fria que viaja con el: ilumina el recibidor al pasar.
luz_fantasma = cmds.pointLight(name="LUZ_fantasma", rgb=(0.6, 0.78, 1.0), intensity=130.0)
luz_fantasma_t = cmds.listRelatives(luz_fantasma, parent=True)[0]
cmds.setAttr(luz_fantasma + ".decayRate", 1)
cmds.setAttr(luz_fantasma + ".useDepthMapShadows", 0)
cmds.move(-45, FANTASMA_ALTO * 0.6, 0, luz_fantasma_t)
# Su luz ilumina la sala pero no a el mismo (de tan cerca lo dejaba quemado),
# y las piezas de la cara no proyectan sombra sobre el cuerpo.
cmds.lightlink(b=True, light=luz_fantasma, object=[cuerpo, boca] + cejas + ojos)
for pieza in [boca] + cejas + ojos:
    cmds.setAttr(cmds.listRelatives(pieza, shapes=True)[0] + ".castsShadows", 0)

ghost_pose = cmds.group(ghost_escala, name="GHOST_pose")
cmds.xform(ghost_pose, pivots=(0, FANTASMA_ALTO * 0.45, 0), worldSpace=True)
ghost_flote = cmds.group(ghost_pose, name="GHOST_flote")
ghost = cmds.group([ghost_flote, luz_fantasma_t], name="GHOST_ruta")
cmds.xform(ghost, pivots=(0, 0, 0), worldSpace=True)

# --- Recorrido. El modelo mira a +X; con rotateY=-90 mira a +Z (la derecha
# vista desde la puerta) y con -180 mira a la camara.
Y_FANTASMA = SUELO_CASA + FANTASMA_FLOTA
cmds.move(FANTASMA_X, Y_FANTASMA, -260, ghost)
clave(ghost, "translateZ", c0, -235, "linear")            # entra atravesando la pared
clave(ghost, "translateZ", c1, PUERTA_Z - 40, "linear")
clave(ghost, "translateZ", d0 + 12, PUERTA_Z, "flat")     # se frena en el centro
clave(ghost, "translateZ", e0, PUERTA_Z, "flat")
clave(ghost, "translateZ", F_HUIDA - 2, PUERTA_Z - 22, "flat")  # se echa atras para coger impulso
clave(ghost, "translateZ", F_HUIDA + 10, PUERTA_Z + 420, "linear")  # y sale disparado por la pared
claves(ghost, "rotateY", [(c0, -90), (d0 + 4, -90), (d0 + 17, -180), (e0, -180), (F_HUIDA - 2, -90)], "flat")

# --- Vaiven: sube y baja suave mientras flota. En el susto, da un bote.
for i, fotograma in enumerate(range(c0, F_SUSTO - 2, 12)):
    clave(ghost_flote, "translateY", fotograma, 6 if i % 2 == 0 else -6)
claves(ghost_flote, "translateY", [(F_SUSTO, -6), (F_SUSTO + 4, 30), (F_SUSTO + 10, 0), (e1, 0)])

# --- Cuerpo: se inclina hacia donde va, se estira en el susto y en la huida.
# (escala en X, escala en Y, escala en Z); X es hacia donde mira.
for fotograma, (sx, sy, sz) in ((c0, (1, 1, 1)), (F_SUSTO - 1, (1, 1, 1)),
                                (F_SUSTO + 1, (1.14, 0.84, 1.14)),   # se encoge un instante
                                (F_SUSTO + 4, (0.8, 1.38, 0.8)),     # y se estira hacia arriba
                                (F_SUSTO + 8, (1.06, 0.94, 1.06)), (F_SUSTO + 12, (1, 1, 1)),
                                (e0, (1, 1, 1)), (F_HUIDA - 2, (0.78, 1.14, 1.1)),   # coge impulso
                                (F_HUIDA + 2, (1.65, 0.74, 0.8)), (e1, (1.65, 0.74, 0.8))):  # estirado al huir
    for canal, valor in zip(("scaleX", "scaleY", "scaleZ"), (sx, sy, sz)):
        clave(ghost_pose, canal, fotograma, valor)
claves(ghost_pose, "rotateZ", [(c0, -6), (d0, -6), (d0 + 9, 5), (d0 + 14, 0), (e0, 0),
                               (F_HUIDA - 2, 12), (F_HUIDA + 2, -24), (e1, -24)])
# Tiembla de miedo tras el susto.
for i, fotograma in enumerate(range(F_SUSTO + 6, e0, 2)):
    clave(ghost_pose, "rotateX", fotograma, 3.5 if i % 2 == 0 else -3.5, "linear")
clave(ghost_pose, "rotateX", F_SUSTO + 4, 0)
clave(ghost_pose, "rotateX", e0, 0)

# --- Cara. Los valores son en unidades del modelo (el cuerpo mide unas 3).
# Cejas: tranquilas -> saltan hacia arriba (sorpresa) -> inclinadas (miedo).
for ceja, lado in zip(cejas, (-1, 1)):
    claves(ceja, "translateY", [(c0, 0), (F_SUSTO, 0), (F_SUSTO + 3, 0.17), (e0, 0.17), (F_HUIDA - 2, 0.1)])
    claves(ceja, "rotateX", [(c0, 0), (e0, 0), (F_HUIDA - 2, lado * 24)])
# Ojos: un parpadeo mientras flota, otro justo al ver al jugador, y se agrandan.
for ojo in ojos:
    alto = [(c0, 1), (c0 + 38, 1), (c0 + 40, 0.1), (c0 + 43, 1),            # parpadeo
            (F_SUSTO - 6, 1), (F_SUSTO - 4, 0.1), (F_SUSTO - 2, 1),         # parpadeo de "no puede ser"
            (F_SUSTO, 1), (F_SUSTO + 3, 1.36), (e1, 1.32)]
    claves(ojo, "scaleY", alto)
    claves(ojo, "scaleZ", [(c0, 1), (F_SUSTO, 1), (F_SUSTO + 3, 1.3), (e1, 1.26)])
    claves(ojo, "translateX", [(c0, 0), (F_SUSTO, 0), (F_SUSTO + 3, 0.03)])  # hacia fuera, para no hundirse
# Boca (es una fila de dientes): normal -> se abre -> mueca ancha al huir.
claves(boca, "scaleY", [(c0, 1), (F_SUSTO, 1), (F_SUSTO + 3, 1.9), (e0, 1.7), (F_HUIDA, 1.5)])
claves(boca, "scaleZ", [(c0, 1), (F_SUSTO, 1), (F_SUSTO + 3, 1.2), (e0, 1.2), (F_HUIDA, 1.4)])
claves(boca, "translateY", [(c0, 0), (F_SUSTO, 0), (F_SUSTO + 3, -0.07)])
claves(boca, "translateX", [(c0, 0), (F_SUSTO, 0), (F_SUSTO + 3, 0.03)])

# =============================================================================
# 4. LAS PUERTAS Y EL INTERIOR
# =============================================================================
# Cada hoja gira sobre su bisagra (el pivote ya viene puesto en el entorno).
# Se abren hacia fuera: una gira en un sentido y la otra en el contrario.
hojas = (("ENT:Hoja_Puerta_DERECHA", 1), ("ENT:Hoja_Puerta_IZQUIERDA", -1))

# --- Quitar el poste central. En el entorno son dos puertas individuales, cada
# una con su marco, y los dos largueros del centro forman un poste en medio del
# hueco. Se copian los marcos a esta escena, se les borra ese larguero y se
# ocultan los originales (el entorno no se toca).
for marco in ("ENT:Marco_Puerta_DERECHA", "ENT:Marco_Puerta_IZQUIERDA"):
    copia_marco = cmds.duplicate(marco, name=marco.split(":")[-1] + "_sin_poste")[0]
    copia_marco = cmds.parent(copia_marco, world=True)[0]
    cmds.setAttr(marco + ".visibility", 0)
    caras_poste = []
    for cara in range(cmds.polyEvaluate(copia_marco, face=True)):
        puntos = cmds.xform("%s.f[%d]" % (copia_marco, cara), query=True, worldSpace=True, translation=True)
        zs, ys = puntos[2::3], puntos[1::3]
        # El larguero central: entre Z=9 y Z=34, por debajo del travesano de arriba.
        if min(zs) >= 9 and max(zs) <= 34 and sum(ys) / len(ys) < SUELO_CASA + 158:
            caras_poste.append("%s.f[%d]" % (copia_marco, cara))
    if caras_poste:
        cmds.delete(caras_poste)
for tope in ("ENT:Tope_Interior_DERECHA_L", "ENT:Tope_Interior_IZQUIERDA_R"):
    cmds.setAttr(tope + ".visibility", 0)
# Las hojas se ensanchan desde su bisagra hasta juntarse en el centro, para
# que al cerrar no quede una rendija donde estaba el poste.
for hoja, _ in hojas:
    bisagra = cmds.xform(hoja, query=True, worldSpace=True, rotatePivot=True)
    x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(hoja)
    borde_libre = z0 if abs(z0 - bisagra[2]) > abs(z1 - bisagra[2]) else z1
    factor = abs(PUERTA_Z - bisagra[2]) / abs(borde_libre - bisagra[2])
    cmds.scale(1, 1, factor, hoja, pivot=bisagra, relative=True)
recorrido = [(a0, 0), (b0 + 6, 0), (b0 + 16, 7), (b0 + 28, 8),      # un chasquido y se entreabre
             (b0 + 54, 68), (b1, ANGULO_ABIERTA),                   # se abre del todo
             (f0 + 12, ANGULO_ABIERTA), (f1, 52),                   # empieza a cerrarse despacio
             (g0, 50)]
for hoja, sentido in hojas:
    base = cmds.getAttr(hoja + ".rotateY")
    claves(hoja, "rotateY", [(f, base + sentido * grados) for f, grados in recorrido])
    # Portazo: cierra de golpe, rebota un poco y se queda.
    clave(hoja, "rotateY", F_PORTAZO, base, "linear")
    clave(hoja, "rotateY", F_PORTAZO + 2, base + sentido * 3.5)
    clave(hoja, "rotateY", F_PORTAZO + 5, base, "flat")
    cmds.keyTangent(hoja, attribute="rotateY", time=(g0, g0), outTangentType="linear")

# Luces del recibidor: calidas, con un parpadeo leve, como bombillas viejas.
luces_interior = []
for nombre, posicion, fuerza in (("LUZ_recibidor_aplique", (-1835, 108, -112), 120.0),
                                 ("LUZ_recibidor_techo", (-1930, 135, 40), 95.0),
                                 ("LUZ_fondo_aplique", (-1715, 108, 146), 110.0)):
    luz = cmds.pointLight(name=nombre, rgb=(1.0, 0.66, 0.34), intensity=fuerza)
    cmds.setAttr(luz + ".decayRate", 1)
    cmds.setAttr(luz + ".useDepthMapShadows", 0)
    luz_t = cmds.listRelatives(luz, parent=True)[0]
    cmds.move(posicion[0], posicion[1], posicion[2], luz_t)
    for fotograma in range(a0, F_FIN + 1, 3):
        clave(luz, "intensity", fotograma, fuerza * random.uniform(0.82, 1.08), "linear")
    luces_interior.append(luz_t)

# =============================================================================
# 5. EL TITULO: el logo aparece sobre las puertas con el portazo
# =============================================================================
ancho_logo = 112.0
img = om.MImage()
img.readFromFile(LOGO)
ancho_px, alto_px = img.getSize()
logo = cmds.polyPlane(name="TITULO_logo", width=ancho_logo, height=ancho_logo * alto_px / float(ancho_px),
                      axis=(-1, 0, 0), subdivisionsX=1, subdivisionsY=1)[0]
cmds.move(PUERTA_X - 26, SUELO_CASA + 84, PUERTA_Z, logo)
mat_logo = cmds.shadingNode("surfaceShader", asShader=True, name="MAT_titulo")
tex_logo = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name="TEX_titulo")
cmds.setAttr(tex_logo + ".fileTextureName", LOGO, type="string")
cmds.connectAttr(tex_logo + ".outColor", mat_logo + ".outColor")
cmds.connectAttr(tex_logo + ".outTransparency", mat_logo + ".outTransparency")
sg_logo = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="MAT_tituloSG")
cmds.connectAttr(mat_logo + ".outColor", sg_logo + ".surfaceShader")
cmds.sets(logo, edit=True, forceElement=sg_logo)
sin_sombras(logo)
# Aparece creciendo de 0, se pasa un poco y vuelve a su tamano: un rebote.
for canal in ("scaleX", "scaleY", "scaleZ"):
    claves(logo, canal, [(F_PORTAZO + 1, 0.001), (F_PORTAZO + 7, 1.18), (F_PORTAZO + 11, 0.95), (F_PORTAZO + 15, 1.0)])
claves(logo, "visibility", [(a0, 0), (F_PORTAZO + 1, 1)], "step")

# =============================================================================
# 6. LAS CAMARAS, una por plano
# La camara es el jugador: va de la furgoneta a la puerta.
# =============================================================================
centro_puerta = (PUERTA_X, SUELO_CASA + 80, PUERTA_Z)

# A: baja, mirando hacia arriba, avanzando despacio. La casa se ve imponente.
cam_a = crear_camara("CAM_A_fachada", focal=20)
clave_camara(cam_a, a0, (-2530, -8, 70), (PUERTA_X, 135, PUERTA_Z), "flat")
clave_camara(cam_a, a1, (-2350, 0, 40), (PUERTA_X, 110, PUERTA_Z), "linear")

# B: mas cerca y casi a la altura de los ojos; las puertas se abren.
cam_b = crear_camara("CAM_B_puertas", focal=28)
clave_camara(cam_b, b0, (-2340, 20, PUERTA_Z), (PUERTA_X, 45, PUERTA_Z), "linear")
clave_camara(cam_b, b1, (-2205, 34, PUERTA_Z), (PUERTA_X, 40, PUERTA_Z), "flat")

# C, D y E: la camara ya ha cruzado el umbral (X_DENTRO), para que el poste
# central del marco de la puerta no tape al fantasma.
# C: deriva un poco hacia donde va el fantasma.
X_DENTRO = PUERTA_X + 24
cam_c = crear_camara("CAM_C_fantasma", focal=20)
clave_camara(cam_c, c0, (X_DENTRO, 45, PUERTA_Z - 25), (FANTASMA_X, 40, PUERTA_Z - 20), "flat")
clave_camara(cam_c, c1, (X_DENTRO, 45, PUERTA_Z + 10), (FANTASMA_X, 40, PUERTA_Z), "flat")

# D: quieta mientras se gira y, en el susto, se echa encima de golpe.
cam_d = crear_camara("CAM_D_susto", focal=28)
cara = (FANTASMA_X, Y_FANTASMA + FANTASMA_ALTO * 0.62, PUERTA_Z)
clave_camara(cam_d, d0, (X_DENTRO, 45, PUERTA_Z + 10), cara, "flat")
clave_camara(cam_d, F_SUSTO - 1, (X_DENTRO + 8, 45, PUERTA_Z + 8), cara, "flat")
clave_camara(cam_d, F_SUSTO + 5, (FANTASMA_X - 125, 50, PUERTA_Z), (cara[0], cara[1] + 12, cara[2]), "flat")
clave_camara(cam_d, d1, (FANTASMA_X - 118, 50, PUERTA_Z), (cara[0], cara[1] + 6, cara[2]), "flat")
sacudir(cam_d, F_SUSTO + 1, F_SUSTO + 14, 2.2)

# E: barrido rapido a la derecha siguiendo la huida; vuelve al recibidor vacio.
cam_e = crear_camara("CAM_E_huida", focal=20)
cmds.move(X_DENTRO, 45, PUERTA_Z, cam_e)
claves(cam_e, "rotateY", [(e0, -90), (F_HUIDA, -90), (F_HUIDA + 6, -126), (F_HUIDA + 18, -93), (e1, -90)])

# F: retrocede saliendo de la casa mientras las puertas empiezan a cerrarse.
cam_f = crear_camara("CAM_F_retirada", focal=28)
clave_camara(cam_f, f0, (-2150, 40, PUERTA_Z), centro_puerta, "flat")
clave_camara(cam_f, f1, (-2335, 32, PUERTA_Z), centro_puerta, "linear")

# G: fija frente a las puertas. Portazo, sacudida y titulo.
cam_g = crear_camara("CAM_G_titulo", focal=35)
clave_camara(cam_g, g0, (-2375, 34, PUERTA_Z), (PUERTA_X, 38, PUERTA_Z), "flat")
clave_camara(cam_g, g1, (-2358, 34, PUERTA_Z), (PUERTA_X, 38, PUERTA_Z), "flat")
sacudir(cam_g, F_PORTAZO, F_PORTAZO + 10, 1.6)

camaras = [cam_a, cam_b, cam_c, cam_d, cam_e, cam_f, cam_g]
cmds.group(camaras + [cielo, luna_geo, halo, logo, cmds.listRelatives(ambiente, parent=True)[0]] + luces_interior,
           name="GRP_animacion_escena3")

try:
    for (nombre, inicio, fin), cam in zip(PLANOS, camaras):
        cmds.shot("PLANO_" + nombre, startTime=inicio, endTime=fin, sequenceStartTime=inicio,
                  sequenceEndTime=fin, currentCamera=cam)
except Exception as error:
    print("No se pudo crear la secuencia de planos: %s" % error)

# =============================================================================
# 6b. VEGETACION A LA IZQUIERDA DE LA CASA
# Mismo metodo que en la escena 2: se copian los modelos del propio entorno
# (arboles, piedras, hierba), se aligeran y se reparten en copias instanciadas.
# =============================================================================
def copia_ligera(prototipo, nombre, reduccion, solo_copa=False):
    copia = cmds.duplicate(prototipo, name=nombre + "_tmp")[0]
    if cmds.listRelatives(copia, parent=True):
        copia = cmds.parent(copia, world=True)[0]
    trozos = [cmds.listRelatives(m, parent=True, fullPath=True)[0]
              for m in cmds.listRelatives(copia, allDescendents=True, type="mesh", fullPath=True)
              if not cmds.getAttr(m + ".intermediateObject")]
    if solo_copa:
        # Para los arbustos: solo las piezas de la mitad de arriba del arbol.
        alto = cmds.exactWorldBoundingBox(copia)[4]
        fuera = [t for t in trozos if cmds.exactWorldBoundingBox(t)[1] < alto * COPA_DESDE]
        trozos = [t for t in trozos if t not in fuera]
        cmds.delete(fuera)
    if len(trozos) > 1:
        malla = cmds.polyUnite(trozos, name=nombre, constructionHistory=False)[0]
    else:
        malla = cmds.rename(cmds.parent(trozos[0], world=True)[0], nombre)
    if cmds.objExists(copia):
        cmds.delete(copia)
    if reduccion > 0:
        cmds.polyReduce(malla, percentage=reduccion, keepQuadsWeight=0, constructionHistory=False)
    # Se deja apoyado en el suelo y centrado en el origen.
    x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(malla)
    cmds.move(-(x0 + x1) / 2.0, -y0, -(z0 + z1) / 2.0, malla, relative=True)
    cmds.makeIdentity(malla, apply=True, translate=True, rotate=True, scale=True)
    cmds.setAttr(malla + ".visibility", 0)  # el molde no se ve; se ven sus copias
    return malla


anadidos = []
ocupado = []


def repartir(cantidad, zonas, moldes, nombre, separacion, tamano):
    """Reparte copias al azar dentro de unas zonas rectangulares (x0, x1, z0, z1)."""
    hechos = intentos = 0
    areas = [(x1 - x0) * (z1 - z0) for x0, x1, z0, z1 in zonas]
    while hechos < cantidad and intentos < cantidad * 60:
        intentos += 1
        x0, x1, z0, z1 = random.choices(zonas, weights=areas)[0]
        x, z = random.uniform(x0, x1), random.uniform(z0, z1)
        if separacion and any(abs(x - ox) < separacion and abs(z - oz) < separacion for ox, oz in ocupado):
            continue
        copia = cmds.instance(random.choice(moldes), name="%s_%03d" % (nombre, len(anadidos)))[0]
        cmds.setAttr(copia + ".visibility", 1)
        escala = random.uniform(tamano[0], tamano[1])
        cmds.move(x, SUELO_Y - 2, z, copia)
        cmds.rotate(0, random.uniform(0, 360), 0, copia)
        cmds.scale(escala, escala * random.uniform(0.9, 1.1), escala, copia)
        if separacion:
            ocupado.append((x, z))
        anadidos.append(copia)
        hechos += 1
    return hechos


pino = copia_ligera("ENT:Prototipo_Arbol_Pino", "ARBOL_ligero_pino", REDUCCION_ARBOLES)
roble = copia_ligera("ENT:Prototipo_Arbol_Roble", "ARBOL_ligero_roble", REDUCCION_ARBOLES)
desnudo = copia_ligera("ENT:Prototipo_Arbol_Desnudo", "ARBOL_ligero_desnudo", 0)
copas = [copia_ligera("ENT:Prototipo_Arbol_Roble", "ARBUSTO_copa_roble", REDUCCION_ARBOLES, solo_copa=True),
         copia_ligera("ENT:Prototipo_Arbol_Pino", "ARBUSTO_copa_pino", REDUCCION_ARBOLES, solo_copa=True)]
piedras = [copia_ligera("ENT:Prototipo_Piedra_%d" % i, "PIEDRA_molde_%d" % i, 0) for i in range(3)]
hierba = [copia_ligera("ENT:Prototipo_Hierba_Alta", "HIERBA_molde", 0)]
mezcla = [pino, pino, roble, roble, desnudo]

# Por capas, de cerca a lejos (visto desde la furgoneta, +X es hacia el fondo
# y -Z la izquierda). El recibidor ocupa de Z=-207 a 248: todo va a su izquierda.
n_medios = repartir(ARBOLES_MEDIOS, [(-1960, -1120, -1000, -520)], mezcla, "ARBOL_medio", 190, (0.75, 1.1))
n_fondo = repartir(ARBOLES_FONDO, [(-2040, -1100, -1800, -950), (-1050, 500, -2400, -1000)], mezcla,
                   "ARBOL_fondo", 230, (1.2, 1.7))
ZONAS_SUELO = [(-2330, -2085, -430, -190), (-2050, -1150, -330, -225), (-2040, -1150, -850, -330)]
n_arbustos = repartir(ARBUSTOS, ZONAS_SUELO, copas, "ARBUSTO", 110, (0.28, 0.48))
n_piedras = repartir(PIEDRAS, ZONAS_SUELO, piedras, "PIEDRA", 0, (0.8, 1.8))
n_hierbas = repartir(HIERBAS, ZONAS_SUELO, hierba, "HIERBA", 0, (0.8, 1.5))
grp_anadidos = cmds.group([pino, roble, desnudo] + copas + piedras + hierba + anadidos,
                          name="GRP_vegetacion_anadida")
print("VEGETACION ANADIDA: %d arboles medios, %d de fondo, %d arbustos, %d piedras, %d hierbas" % (
    n_medios, n_fondo, n_arbustos, n_piedras, n_hierbas))

# =============================================================================
# 7. OPTIMIZACION: ocultar lo que ninguna camara ve (el entorno no se modifica)
# =============================================================================
def caras_dibujadas(raices):
    visibles = {}

    def visible(ruta):
        if ruta not in visibles:
            padre = ruta.rsplit("|", 1)[0]
            visibles[ruta] = bool(cmds.getAttr(ruta + ".visibility")) and (not padre or visible(padre))
        return visibles[ruta]

    return sum(cmds.polyEvaluate(f, face=True)
               for f in cmds.ls(raices, dag=True, type="mesh", noIntermediate=True, long=True, allPaths=True)
               if visible(f))


caras_casa_antes = caras_dibujadas(["ENT:CASA"])
caras_vegetacion_antes = caras_dibujadas(["ENT:Arboles_y_Vegetacion"])

# --- Casa: el recibidor (Room_Finish) se deja amueblado porque se ve por
# dentro. Del resto de habitaciones solo quedan muros, ventanas y postes.
CONSERVAR_EN_CASA = ("Wall", "Door", "Window", "Post")
QUITAR_EN_CASA = ("Lamp", "Light")
# Unas puertas antiguas fijas que ocupan el mismo hueco que las que se abren,
# y una mesilla muy pesada que queda fuera de la vista.
QUITAR_DEL_RECIBIDOR = ("ENT:Door", "ENT:Door__1__1", "ENT:Bedside_Table")
for forma in cmds.ls("ENT:CASA", dag=True, type="mesh", noIntermediate=True, long=True, allPaths=True):
    dentro = forma.split("|ENT:CASA|", 1)[-1]
    padre = cmds.listRelatives(forma, parent=True, fullPath=True)[0]
    if dentro.startswith("ENT:Room_Finish|"):
        ocultar = any(("|%s|" % nombre) in ("|" + dentro) for nombre in QUITAR_DEL_RECIBIDOR)
    else:
        ocultar = (not any(c in dentro for c in CONSERVAR_EN_CASA)) or any(c in dentro for c in QUITAR_EN_CASA)
    if ocultar:
        cmds.setAttr(padre + ".visibility", 0)

# --- Vegetacion: se oculta la que no entra en el encuadre de ninguna camara.
def hijos(nodo):
    return cmds.listRelatives(nodo, children=True, type="transform", fullPath=True) or []


candidatos = []
for grupo in ("ENT:Arboles_Instanciados", "ENT:Bosque_Perimetral_Instanciado", "ENT:Arbustos_Instanciados",
              "ENT:Hierbas_Instanciadas"):
    candidatos += hijos(grupo)
for grupo in ("ENT:Vegetacion_Prolongacion", "ENT:Vegetacion_Tramo_Entrada"):
    for subgrupo in hijos(grupo):
        candidatos += hijos(subgrupo)
datos = []
for planta in candidatos:
    x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(planta)
    datos.append((planta, ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0), max(x1 - x0, y1 - y0, z1 - z0) / 2.0))
vistas = set()
for (nombre, inicio, fin), cam in zip(PLANOS, camaras):
    forma_cam = cmds.listRelatives(cam, shapes=True)[0]
    focal = cmds.getAttr(forma_cam + ".focalLength")
    tan_h = cmds.getAttr(forma_cam + ".horizontalFilmAperture") * 25.4 / 2.0 / focal * MARGEN_ENCUADRE
    tan_v = cmds.getAttr(forma_cam + ".verticalFilmAperture") * 25.4 / 2.0 / focal * MARGEN_ENCUADRE
    for fotograma in range(inicio, fin + 1, 4):
        cmds.currentTime(fotograma)
        a_camara = om.MMatrix(cmds.xform(cam, query=True, worldSpace=True, matrix=True)).inverse()
        for i, (planta, centro_planta, radio) in enumerate(datos):
            if i in vistas:
                continue
            p = om.MPoint(centro_planta) * a_camara
            profundidad = -p.z
            if profundidad < -radio:
                continue
            profundidad = max(profundidad, 1.0)
            if abs(p.x) <= profundidad * tan_h + radio and abs(p.y) <= profundidad * tan_v + radio:
                vistas.add(i)
for i, (planta, _, _) in enumerate(datos):
    if i not in vistas:
        cmds.setAttr(planta + ".visibility", 0)

print("OPTIMIZACION - caras que se dibujan (antes -> despues)")
print("  Casa:        %7d -> %7d" % (caras_casa_antes, caras_dibujadas(["ENT:CASA"])))
print("  Vegetacion:  %7d -> %7d  (%d de %d plantas a la vista)" % (
    caras_vegetacion_antes, caras_dibujadas(["ENT:Arboles_y_Vegetacion"]), len(vistas), len(datos)))
print("  Fantasma: piezas %s" % ", ".join([cuerpo, boca] + cejas + ojos))

# =============================================================================
# 8. AJUSTES DE TIEMPO E IMAGEN
# =============================================================================
cmds.currentUnit(time="film")  # "film" = 24 fotogramas por segundo
cmds.playbackOptions(minTime=1, maxTime=F_FIN, animationStartTime=1, animationEndTime=F_FIN)
cmds.setAttr("defaultResolution.width", 1920)
cmds.setAttr("defaultResolution.height", 1080)
cmds.setAttr("defaultResolution.deviceAspectRatio", 1920.0 / 1080.0)
cmds.setAttr("defaultRenderGlobals.startFrame", 1)
cmds.setAttr("defaultRenderGlobals.endFrame", F_FIN)
cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
cmds.setAttr("perspShape.renderable", 0)
cmds.setAttr(cmds.listRelatives(cam_a, shapes=True)[0] + ".renderable", 1)

# =============================================================================
# 9. GUARDAR
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
    for panel in cmds.getPanel(type="modelPanel"):
        if cmds.modelPanel(panel, query=True, camera=True).startswith("persp"):
            cmds.lookThru(panel, cam_a)
            cmds.modelEditor(panel, edit=True, displayAppearance="smoothShaded",
                             displayTextures=True, displayLights="all")
