# -*- coding: utf-8 -*-
"""
PickABoo - Trailer - ESCENA 1: la oficina y el telefono que suena.

Monta la oficina, coloca el telefono, crea la camara y anima todo el plano.
Al terminar guarda animaciones/escenas/escena1_oficina.ma

Como ejecutarlo dentro de Maya:
    Windows > General Editors > Script Editor, pestana Python, y pegar:
        exec(open(r"C:/Users/Alejandro/Desktop/Modelos3DMaya/animaciones/scripts/escena1_oficina.py", encoding="utf-8").read())

OJO: el script empieza una escena nueva. Si tienes cambios sin guardar, Maya
se negara a continuar para no perderlos; guarda primero y vuelve a ejecutar.
"""
import os

import maya.cmds as cmds

# Con mayapy (Maya sin ventana) hay que arrancar el motor a mano.
# Dentro de Maya normal los comandos ya existen y esto se salta.
_SIN_VENTANA = not hasattr(cmds, "polyCube")
if _SIN_VENTANA:
    import maya.standalone
    maya.standalone.initialize(name="python")

import maya.api.OpenMaya as om

# =============================================================================
# AJUSTES: lo que mas vas a querer tocar esta aqui arriba.
# Unidades en centimetros. Y es arriba, X es izquierda/derecha, Z es hacia camara.
# =============================================================================
# Carpeta "animaciones" del repositorio. Se deduce de donde esta este script;
# al pegarlo con exec() en el Script Editor eso no se puede saber y se usa la
# ruta fija de abajo (cambiala si el repositorio esta en otro sitio).
try:
    ANIMACIONES = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
except NameError:
    ANIMACIONES = "C:/Users/Alejandro/Desktop/Modelos3DMaya/animaciones"
CARPETA_MODELOS = ANIMACIONES + "/modelos"
# Copia del logo con el fondo blanco de fuera convertido en transparente.
LOGO = CARPETA_MODELOS + "/logo_pickaboo_transparente.png"
# Modelo descargado del telefono y su textura de color. Si el archivo no
# existe, el script crea un telefono provisional con cajas.
TELEFONO_MODELO = CARPETA_MODELOS + "/landline-phone/source/landline phone.fbx"
TELEFONO_TEXTURA = CARPETA_MODELOS + "/landline-phone/textures/tel_fijo_color.jpg"
TELEFONO_GIRO_Y = 0.0  # grados; cambialo si el telefono no mira a camara
SALIDA = ANIMACIONES + "/escenas/escena1_oficina.ma"

FPS = 24
F_INICIO = 1
F_FIN_PANEO = 168      # 7 s: la camara termina de desplazarse a la izquierda
F_FIN = 264            # 11 s: la camara termina de acercarse al logo

# Posicion de la camara (x, y, z) y su inclinacion en grados (negativo = mira
# hacia abajo) en cada momento clave.
CAM_INICIO = (160.0, 160.0, 360.0, -7.0)     # se ve el mostrador y la puerta
CAM_FIN_PANEO = (-70.0, 160.0, 360.0, -7.0)  # el logo asoma por la izquierda
CAM_FINAL = (-230.0, 160.0, 280.0, 0.0)      # el logo llena el encuadre

# Cada pareja es (fotograma en que empieza, fotograma en que acaba) un "piiip".
TIMBRAZOS = [(1, 14), (22, 35), (60, 73), (81, 94)]
# Desde aqui la luz se queda fija: esta sonando el mensaje del contestador.
LUZ_FIJA_DESDE = 110

LOGO_X, LOGO_Y, LOGO_ANCHO = -230.0, 160.0, 170.0
TELEFONO_X, TELEFONO_ANCHO = 50.0, 38.0  # algo mas grande que uno real para que se lea en plano
ALTURA_MOSTRADOR = 96.0


# =============================================================================
# FUNCIONES DE AYUDA
# =============================================================================
def material(nombre, color):
    """Crea un material de color liso y devuelve su shading group.
    En Maya un objeto no se conecta al material directamente, sino a un
    'shading group' que es quien junta material y geometria."""
    mat = cmds.shadingNode("lambert", asShader=True, name="MAT_" + nombre)
    cmds.setAttr(mat + ".color", color[0], color[1], color[2], type="double3")
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=mat + "SG")
    cmds.connectAttr(mat + ".outColor", sg + ".surfaceShader")
    return sg


def caja(nombre, ancho, alto, fondo, posicion, sg):
    obj = cmds.polyCube(name=nombre, width=ancho, height=alto, depth=fondo)[0]
    cmds.move(posicion[0], posicion[1], posicion[2], obj)
    cmds.sets(obj, edit=True, forceElement=sg)
    return obj


def tamano_imagen(ruta):
    img = om.MImage()
    img.readFromFile(ruta)
    return img.getSize()


def importar_telefono(ruta, textura):
    """Importa el modelo descargado, le pone su textura, lo escala a
    TELEFONO_ANCHO y lo deja apoyado en el origen (centrado en X/Z y con la
    base en Y=0)."""
    ext = os.path.splitext(ruta)[1].lower()
    if ext == ".fbx":
        cmds.loadPlugin("fbxmaya", quiet=True)
    elif ext == ".obj":
        cmds.loadPlugin("objExport", quiet=True)
    nuevos = cmds.file(ruta, i=True, returnNewNodes=True, namespace="tel")
    raices = cmds.ls(nuevos, assemblies=True)
    modelo = cmds.group(raices, name="telefono_modelo")

    # El FBX llega con un material sin textura: se le conecta la imagen de color.
    if os.path.isfile(textura):
        tex = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name="TEX_telefono")
        cmds.setAttr(tex + ".fileTextureName", textura, type="string")
        for sg in cmds.ls(nuevos, type="shadingEngine"):
            for mat in cmds.listConnections(sg + ".surfaceShader") or []:
                cmds.connectAttr(tex + ".outColor", mat + ".color", force=True)

    cmds.rotate(0, TELEFONO_GIRO_Y, 0, modelo)
    # Los modelos de internet vienen en cualquier escala: se mide y se ajusta.
    x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(modelo)
    escala = TELEFONO_ANCHO / max(x1 - x0, z1 - z0)
    cmds.scale(escala, escala, escala, modelo, pivot=(0, 0, 0))
    x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(modelo)
    cmds.move(-(x0 + x1) / 2.0, -y0, -(z0 + z1) / 2.0, modelo, relative=True)
    return modelo


def telefono_provisional(sg_cuerpo, sg_teclas):
    """Telefono hecho con cajas, para trabajar mientras no hay modelo real."""
    piezas = [
        caja("TELEFONO_base", TELEFONO_ANCHO, 6, 20, (0, 3, 0), sg_cuerpo),
        caja("TELEFONO_auricular", 8, 4, 22, (-9, 8, 0), sg_cuerpo),
        caja("TELEFONO_teclado", 12, 1, 12, (5, 6.5, 1), sg_teclas),
    ]
    return cmds.group(piezas, name="telefono_modelo")


# =============================================================================
# 1. ESCENA NUEVA Y AJUSTES GENERALES
# =============================================================================
try:
    cmds.file(new=True)
except RuntimeError:
    raise RuntimeError("Tienes cambios sin guardar en Maya. Guarda la escena y vuelve a ejecutar el script.")

cmds.currentUnit(time="film")  # "film" = 24 fotogramas por segundo
cmds.playbackOptions(minTime=F_INICIO, maxTime=F_FIN, animationStartTime=F_INICIO, animationEndTime=F_FIN)
cmds.setAttr("defaultResolution.width", 1920)
cmds.setAttr("defaultResolution.height", 1080)
cmds.setAttr("defaultResolution.deviceAspectRatio", 1920.0 / 1080.0)
cmds.setAttr("defaultRenderGlobals.startFrame", F_INICIO)
cmds.setAttr("defaultRenderGlobals.endFrame", F_FIN)

# =============================================================================
# 2. LA OFICINA
# =============================================================================
sg_pared = material("pared", (0.42, 0.47, 0.45))
sg_suelo = material("suelo", (0.22, 0.17, 0.13))
sg_madera = material("madera", (0.33, 0.21, 0.12))
sg_tablero = material("tablero", (0.55, 0.42, 0.28))  # claro, para que el telefono negro destaque
sg_puerta = material("puerta", (0.27, 0.19, 0.13))
sg_marco = material("marco", (0.12, 0.09, 0.07))
sg_cristal = material("cristal", (0.55, 0.65, 0.7))
sg_telefono = material("telefono", (0.08, 0.08, 0.09))
sg_teclas = material("teclas", (0.6, 0.6, 0.58))
sg_maceta = material("maceta", (0.6, 0.3, 0.18))
sg_planta = material("planta", (0.15, 0.4, 0.15))
sg_figura = material("figura", (0.75, 0.65, 0.3))

pared = cmds.polyPlane(name="pared_fondo", width=1000, height=320, axis=(0, 0, 1),
                       subdivisionsX=1, subdivisionsY=1)[0]
cmds.move(0, 160, 0, pared)
cmds.sets(pared, edit=True, forceElement=sg_pared)

suelo = cmds.polyPlane(name="suelo", width=1000, height=700, axis=(0, 1, 0),
                       subdivisionsX=1, subdivisionsY=1)[0]
cmds.move(0, 0, 350, suelo)
cmds.sets(suelo, edit=True, forceElement=sg_suelo)

mostrador = [
    caja("mostrador_cuerpo", 240, 90, 70, (100, 45, 50), sg_madera),
    caja("mostrador_tablero", 256, 6, 82, (100, 93, 52), sg_tablero),
]

puerta = [
    caja("puerta_marco", 112, 222, 4, (330, 111, 2), sg_marco),
    caja("puerta_hoja", 92, 210, 6, (330, 105, 4), sg_puerta),
]
ventana = cmds.polyCylinder(name="puerta_ventana", radius=18, height=7, axis=(0, 0, 1))[0]
cmds.move(330, 150, 4.5, ventana)
cmds.sets(ventana, edit=True, forceElement=sg_cristal)
puerta.append(ventana)

# Planta y figurita provisionales sobre el mostrador.
maceta = cmds.polyCylinder(name="planta_maceta", radius=9, height=14)[0]
cmds.move(165, ALTURA_MOSTRADOR + 7, 55, maceta)
cmds.sets(maceta, edit=True, forceElement=sg_maceta)
planta = [maceta]
for i, giro in enumerate((-25, 0, 25, -12, 14)):
    hoja = cmds.polyCone(name="planta_hoja_%d" % (i + 1), radius=3, height=26)[0]
    cmds.xform(hoja, pivots=(0, -13, 0))
    cmds.move(165, ALTURA_MOSTRADOR + 27, 55, hoja)
    cmds.rotate(giro * 0.6, i * 72, giro, hoja)
    cmds.sets(hoja, edit=True, forceElement=sg_planta)
    planta.append(hoja)

cuerpo = cmds.polyCylinder(name="figurita_cuerpo", radius=3, height=10)[0]
cmds.move(125, ALTURA_MOSTRADOR + 5, 60, cuerpo)
cabeza = cmds.polySphere(name="figurita_cabeza", radius=3.5)[0]
cmds.move(125, ALTURA_MOSTRADOR + 13, 60, cabeza)
cmds.sets([cuerpo, cabeza], edit=True, forceElement=sg_figura)

# =============================================================================
# 3. EL LOGO EN LA PARED
# Un plano con la imagen como textura. El PNG tiene fondo transparente, y esa
# transparencia se conecta al material para que no se vea un cuadrado blanco.
# =============================================================================
ancho_px, alto_px = tamano_imagen(LOGO)
logo = cmds.polyPlane(name="logo_pared", width=LOGO_ANCHO, height=LOGO_ANCHO * alto_px / float(ancho_px),
                      axis=(0, 0, 1), subdivisionsX=1, subdivisionsY=1)[0]
cmds.move(LOGO_X, LOGO_Y, 1, logo)  # 1 cm por delante de la pared para que no parpadee

mat_logo = cmds.shadingNode("lambert", asShader=True, name="MAT_logo")
sg_logo = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="MAT_logoSG")
cmds.connectAttr(mat_logo + ".outColor", sg_logo + ".surfaceShader")
tex_logo = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name="TEX_logo")
cmds.setAttr(tex_logo + ".fileTextureName", LOGO, type="string")
cmds.connectAttr(tex_logo + ".outColor", mat_logo + ".color")
cmds.connectAttr(tex_logo + ".outTransparency", mat_logo + ".transparency")
cmds.setAttr(mat_logo + ".diffuse", 1.0)
cmds.sets(logo, edit=True, forceElement=sg_logo)
if cmds.attributeQuery("aiOpaque", node=cmds.listRelatives(logo, shapes=True)[0], exists=True):
    cmds.setAttr(cmds.listRelatives(logo, shapes=True)[0] + ".aiOpaque", 0)  # para Arnold

# =============================================================================
# 4. EL TELEFONO
# Si existe el modelo descargado (TELEFONO_MODELO) se usa ese. Si no, se crea
# uno provisional con cajas.
# =============================================================================
if os.path.isfile(TELEFONO_MODELO):
    print("Usando el modelo de telefono: " + TELEFONO_MODELO)
    modelo_telefono = importar_telefono(TELEFONO_MODELO, TELEFONO_TEXTURA)
else:
    print("No existe " + TELEFONO_MODELO + "; se usa un telefono provisional.")
    modelo_telefono = telefono_provisional(sg_telefono, sg_teclas)

# Lucecita del contestador: una esfera pequena con su propio material, para
# poder animar su brillo sin afectar al resto del telefono.
mat_led = cmds.shadingNode("lambert", asShader=True, name="MAT_led")
cmds.setAttr(mat_led + ".color", 0.15, 0.0, 0.0, type="double3")
sg_led = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="MAT_ledSG")
cmds.connectAttr(mat_led + ".outColor", sg_led + ".surfaceShader")
alto_telefono = cmds.exactWorldBoundingBox(modelo_telefono)[4]
led = cmds.polySphere(name="telefono_led", radius=1.2)[0]
cmds.move(10, alto_telefono + 0.5, -6, led)
cmds.sets(led, edit=True, forceElement=sg_led)

# Luz roja que tine el mostrador cuando el LED se enciende. Con decayRate=2 la
# luz pierde fuerza con la distancia, asi solo ilumina alrededor del telefono.
luz_led = cmds.pointLight(name="LUZ_led", rgb=(1.0, 0.1, 0.05), intensity=0.0)
luz_led_t = cmds.listRelatives(luz_led, parent=True)[0]
cmds.setAttr(luz_led + ".decayRate", 2)
cmds.move(10, alto_telefono + 8, -6, luz_led_t)

# Todo lo del telefono va en un grupo. Se anima el grupo, no las piezas: asi
# puedes cambiar el modelo de dentro sin perder la animacion.
grp_telefono = cmds.group([modelo_telefono, led, luz_led_t], name="GRP_telefono")
cmds.xform(grp_telefono, pivots=(0, 0, 0), worldSpace=True)
cmds.move(TELEFONO_X, ALTURA_MOSTRADOR, 55, grp_telefono)

# =============================================================================
# 5. ORDEN EN EL OUTLINER
# =============================================================================
cmds.group([pared, suelo], name="GRP_sala")
cmds.group(mostrador, name="GRP_mostrador")
cmds.group(puerta, name="GRP_puerta")
cmds.group(planta, name="GRP_planta")
cmds.group([cuerpo, cabeza], name="GRP_figurita")
cmds.group(logo, name="GRP_logo")

# =============================================================================
# 6. LUCES DE LA SALA: oficina a oscuras, de noche.
# =============================================================================
ambiente = cmds.ambientLight(name="LUZ_ambiente", rgb=(0.55, 0.65, 0.9), intensity=0.45)
principal = cmds.directionalLight(name="LUZ_principal", rgb=(1.0, 0.92, 0.8), intensity=0.9)
cmds.rotate(-35, 25, 0, cmds.listRelatives(principal, parent=True)[0])
cmds.group([cmds.listRelatives(ambiente, parent=True)[0], cmds.listRelatives(principal, parent=True)[0]],
           name="GRP_luces")

# =============================================================================
# 7. CAMARA
# =============================================================================
cam, cam_forma = cmds.camera(focalLength=35, horizontalFilmAperture=1.417, verticalFilmAperture=0.797,
                             nearClipPlane=1, farClipPlane=5000)
cam = cmds.rename(cam, "CAM_escena1")
cam_forma = cmds.listRelatives(cam, shapes=True)[0]
cmds.setAttr(cam_forma + ".displayResolution", 1)  # dibuja el marco del encuadre
cmds.setAttr(cam_forma + ".renderable", 1)
cmds.setAttr("perspShape.renderable", 0)

# =============================================================================
# 8. ANIMACION DE LA CAMARA
# Un keyframe guarda "en este fotograma, este valor". Maya rellena lo de en medio.
# =============================================================================
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
# 9. ANIMACION DEL TELEFONO: luz y vibracion en cada timbrazo
# =============================================================================
LUZ_ENCENDIDA = 2500.0  # alta porque la luz se atenua con el cuadrado de la distancia


def luz(fotograma, encendida):
    cmds.setKeyframe(mat_led, attribute="incandescenceR", time=fotograma, value=1.0 if encendida else 0.0)
    cmds.setKeyframe(luz_led, attribute="intensity", time=fotograma, value=LUZ_ENCENDIDA if encendida else 0.0)


luz(F_INICIO, False)
for empieza, acaba in TIMBRAZOS:
    luz(empieza, True)
    luz(acaba + 1, False)
    # Vibracion: el telefono se inclina a un lado y a otro cada 2 fotogramas.
    cmds.setKeyframe(grp_telefono, attribute="rotateZ", time=empieza - 1, value=0)
    for i, fotograma in enumerate(range(empieza, acaba + 1, 2)):
        cmds.setKeyframe(grp_telefono, attribute="rotateZ", time=fotograma, value=1.5 if i % 2 == 0 else -1.5)
    cmds.setKeyframe(grp_telefono, attribute="rotateZ", time=acaba + 1, value=0)
luz(LUZ_FIJA_DESDE, True)

# "step" = el valor salta de golpe en vez de ir subiendo poco a poco: una luz
# que parpadea se enciende y se apaga, no hace fundidos.
cmds.keyTangent(mat_led, attribute="incandescenceR", outTangentType="step")
cmds.keyTangent(luz_led, attribute="intensity", outTangentType="step")

# =============================================================================
# 10. GUARDAR
# =============================================================================
cmds.currentTime(F_INICIO)
cmds.select(clear=True)
for carpeta in (os.path.dirname(SALIDA), CARPETA_MODELOS):
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
cmds.file(rename=SALIDA)
cmds.file(save=True, type="mayaAscii")
print("Escena guardada en " + SALIDA)

if _SIN_VENTANA:
    maya.standalone.uninitialize()
else:
    # Dentro de Maya: mirar por la camara del plano con luces y texturas activas.
    for panel in cmds.getPanel(type="modelPanel"):
        if cmds.modelPanel(panel, query=True, camera=True).startswith("persp"):
            cmds.lookThru(panel, cam)
            cmds.modelEditor(panel, edit=True, displayAppearance="smoothShaded",
                             displayTextures=True, displayLights="all")
