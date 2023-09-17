import urllib.request
from pymongo import MongoClient
import cv2
from tkinter import *
from PIL import Image, ImageTk
import time
from tkscrolledframe import ScrolledFrame


app = Tk()
app.geometry("700x600")

connection_string = "mongodb+srv://mivotoapi:mivotoapi123@mivoto.n4q9rmw.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)
db = client.MiVoto

cam = cv2.VideoCapture(0)


fotoNoSacada = True
dniNoIngresado = True

candidato = ""
dni = None
fotoUrl = "https://i.imgur.com/XFi08aI.jpg"
estadoVoto = False
esAdmin = False

def camarasDisponibles():
    is_working = True
    dev_port = 0
    working_ports = []
    while is_working:
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            is_working = False
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                working_ports.append(dev_port)
        dev_port +=1
    return working_ports

def borrarPantalla():
    for widget in app.winfo_children():
        if isinstance(widget, Label):
            if widget._name != "titulo":
                widget.pack_forget()
        else:
            widget.pack_forget()
    for widget in scroll.winfo_children():
        widget.pack_forget()

def votarPresidente():

    global botonConfVoto
    borrarPantalla()

    titulo = Label(app, text="Candidatos a Presidente")
    titulo.pack(pady=10)

    sf["width"] = 640
    sf["height"] = 210
    sf.pack(side="top", expand=0, fill=None)

    mostrarCandidatos("Pais")
    botonConfVoto.pack(fill=None,pady=10)

def votarGobernador():
    global botonConfVoto
    global dni

    borrarPantalla()

    titulo = Label(app, text="Candidatos a Gobernador")
    titulo.pack(pady=10)
    sf["width"] = 640
    sf["height"] = 210
    sf.pack(side="top", expand=0, fill=None)

    collection = db.usuario
    myquery = { "dni": dni }
    resp = collection.find(myquery)
    localidad = resp[0]["local"]

    mostrarCandidatos(localidad)
    botonConfVoto.pack(fill=None,pady=10)

def votarCandidato():
    global candidato
    global dni

    myquery = { "nombreC": candidato }
    newvalues = { "$inc": { "cantVotos": 1 } }
    collection = db.candidatos
    collection.update_one(myquery, newvalues)

    myquery = { "dni": dni }

    if not(getValorDeUsuario(dni,"estadoVoto")):
        newvalues = { "$set": { "estadoVoto": True } }
        collection = db.usuario
        collection.update_one(myquery, newvalues)
        votarGobernador()
    else:
        if esAdmin:
            opcionesAdmin()
        else:
            ingresarDni()

def setCandidato(a):
    global botonConfVoto
    global candidato
    candidato = a
    botonConfVoto["text"] = "Votar a " + a
    botonConfVoto["bg"] = "green"
    app.update()

def mostrarMensaje(malo, msg):
	if malo:
		mensaje = Label(app, text = msg, fg='red')
	else:
		mensaje = Label(app, text = msg, fg='green')
	mensaje.pack(pady= (10,0))
	app.update()
	time.sleep(2)
	mensaje.pack_forget()

def ingresarCandidato():
    def ingBD():
        nombreP = entP.get()
        nombreC = entC.get()
        localidad = entLoca.get()
        politicas = entPol.get()
        imgLink = entImg.get()
        colP = entColP.get()

        document = {"nombreP": nombreP, "nombreC": nombreC, "localidad": localidad, "politicas":politicas,"imgLink": imgLink,"colorP": colP, "cantVotos": 0} 
        try:
            collection = db.candidatos
            collection.insert_one(document)
            mostrarMensaje(False,"Se ingreso correctamente")
            opcionesAdmin()
        except:
            print("ocurrio un error")
    
    borrarPantalla()
    Label(app, text= "Nombre del partido").pack()
    entP= Entry(app)
    entP.pack()
    Label(app, text= "Nombre del candidato").pack()
    entC= Entry(app)
    entC.pack()
    Label(app, text= "Localidad").pack()
    entLoca= Entry(app)
    entLoca.pack()
    Label(app, text= "Politicas").pack()
    entPol= Entry(app)
    entPol.pack()
    Label(app, text= "Link de la imagen").pack()
    entImg= Entry(app)
    entImg.pack()
    Label(app, text= "Color del partido (HEX)").pack()
    entColP= Entry(app)
    entColP.pack()
    
    Button(app, text="Crear candidato", command= ingBD).pack(pady=20)
    Button(app, text="Cancelar", command= opcionesAdmin).pack(pady=20)

def ingresarPersona():
    inEsAdmin = False
    def ingBD():
        inDni = int(entDni.get())
        inFotoUrl = entFoto.get()
        loca = entLoca.get()
        document = {"dni": inDni, "foto": inFotoUrl, "estadoVoto": False, "local" : loca, "admin": inEsAdmin} 
        try:
            collection = db.usuario
            collection.insert_one(document)
            mostrarMensaje(False,"Se ingreso correctamente")
            opcionesAdmin()
            
        except:
            print("ocurrio un error")
    
    borrarPantalla()
    Label(app, text= "DNI").pack()
    entDni= Entry(app)
    entDni.pack()
    Label(app, text= "Link de la foto").pack()
    entFoto= Entry(app)
    entFoto.pack()
    Label(app, text= "Localidad").pack()
    entLoca= Entry(app)
    entLoca.pack()
    
    entEsAdmin = Checkbutton(app, text = "Admin", variable = inEsAdmin, onvalue = True, offvalue = False, height=3)
    entEsAdmin.pack()
    
    Button(app, text="Crear usuario", command= ingBD).pack(pady=20)
    Button(app, text="Cancelar", command= opcionesAdmin).pack(pady=20)

def verResultados(localidad):
    borrarPantalla()

    def graficoTorta(PieV,colV):
        canvas = Canvas(app,width=200,height=200)
        canvas.pack(side="top", pady=10)
        st = 0
        coord = 0, 0, 200, 200
        for val,col in zip(PieV,colV):    
            canvas.create_arc(coord,start=st,extent = val*3.6,fill=col,outline=col)
            st = st + val*3.6 

    def crearBarraCandidato(candidato):
        global scroll
        colorP= candidato["colorP"]
        Boleta = LabelFrame(scroll,bg=colorP)
        nombreCand = Label(Boleta, text=candidato["nombreC"]+": "+ str(candidato["cantVotos"])+ " votos", bg= colorP)
        Boleta.pack(fill=None,expand=False,side="top")
        nombreCand.pack(side="left")

    collection = db.candidatos
    myquery = { "localidad": localidad }
    candidatos = collection.find(myquery)
    votosTotal = 0
    long= []
    colores= []
    lastColor = "#CAD0D6"

    for y in candidatos:
        votosTotal += int(y["cantVotos"])

    candidatos = collection.find(myquery)
    resto = 100
    
    for x in candidatos:
        if votosTotal < 0:
            porcentaje = int((x["cantVotos"] *100) / votosTotal)
            resto = resto - porcentaje
            long.append(porcentaje)
            colores.append(x["colorP"])
            lastColor = x["colorP"]
        else:
            long.append(100)
            colores.append("#CAD0D6")
            break

    long.append(resto)
    colores.append(lastColor)
    graficoTorta(long, colores)

    candidatos = collection.find(myquery)

    sf["width"] = 200
    sf["height"] = 250
    sf.pack(expand=0, fill=None)

    for x in candidatos:
        crearBarraCandidato(x)
    
    Button(app, text= "Volver", command= opcionesAdmin).pack(pady= 20)

def verPadron():
    borrarPantalla()

    def crearBarraCandidato(usuario):
        global scroll
        colorP = "Red"
        estadoVoto = " no voto"
        if usuario["estadoVoto"]:
            colorP = "Green"
            estadoVoto = " voto"
        Boleta = LabelFrame(scroll,bg=colorP)
        nombreUsu = Label(Boleta, text=str(usuario["dni"]) + estadoVoto, bg= colorP)
        Boleta.pack(fill=None,expand=False,side="top")
        nombreUsu.pack(side="left")

    collection = db.usuario

    filtroVoto = { "estadoVoto": True }
    filtroNoVoto = { "estadoVoto": False }

    cantVotos = collection.count_documents(filtroVoto)
    cantNoVoto = collection.count_documents(filtroNoVoto)

    Label(app, text= "Cantidad de votantes: " + str(cantVotos), fg="Green").pack(pady= 10)
    Label(app, text= "Cantidad de no votantes: " + str(cantNoVoto), fg="Red").pack()
    Label(app, text= "Lista:").pack(pady=20)
    sf["width"] = 150
    sf["height"] = 250
    sf.pack(expand=0, fill=None)
    
    candidatos = collection.find()

    for x in candidatos:
        crearBarraCandidato(x)
    
    Button(app, text= "Volver", command= opcionesAdmin).pack(pady= 20)

def imgPorLink(link,nombre):
    urllib.request.urlretrieve(link, nombre)

def compararCarasFotos(img1, img2):
   time.sleep(2)
   return True

def getValorDeUsuario(dni, valor):
    try:
        collection = db.usuario
        myquery = { "dni": dni }
        resp = collection.find(myquery)
        return resp[0][valor]
    except:
        return None

def opcionesAdmin():
    borrarPantalla()
    def elegirLocalidad():
        borrarPantalla()
        Label(app, text= "Ingrese la localidad de la cual quiere ver los votos").pack()
        entLoc = Entry(app)
        entLoc.pack()
        Button(app, text="Aceptar", command= lambda: verResultados(entLoc.get())).pack()
        
    if not(getValorDeUsuario(dni, "estadoVoto")):
        votarPresidente()
    else:
        Button(app, text="Ver Resultados", command= elegirLocalidad).pack(pady=20)
        Button(app, text="Añadir candidato", command= ingresarCandidato).pack(pady=20)
        Button(app, text="Ver Padron", command= verPadron).pack(pady=20)
        Button(app, text="Añadir usuario", command= ingresarPersona).pack(pady=20)

def sacarFotoYComparar(cam):
    global fotoNoSacada
    result, image = cam.read()
    if result:
        resize = cv2.resize(image, (1920, 1080))
        cv2.imwrite("retratoCam.jpg", resize)
        imgPorLink(getValorDeUsuario(dni,"foto"),"retratoUrl.jpg")
        if compararCarasFotos("retratoCam.jpg","retratoUrl.jpg"):
            fotoNoSacada = False
            if esAdmin:
                opcionesAdmin()
            else:
                votarPresidente()
        else:
            mostrarMensaje(True, "No se logro confirmar su identidad. Vuelva a sacar la foto")
    else:
        mostrarMensaje(True, "No se logro confirmar su identidad. Vuelva a sacar la foto")

def crearBotonCandidato(x):
    global scroll
    colorP= x["colorP"]
    Boleta = LabelFrame(scroll,bg=colorP)
    nombrePart = Label(Boleta, text=x["nombreP"], bg=colorP)
    nombreCand = Label(Boleta, text=x["nombreC"], bg= colorP)
    nombreArch= "boleta-"+ x["nombreC"]+".jpg"
    imgPorLink(x["imgLink"], nombreArch)
    img= Image.open(nombreArch)
    resized_img = img.resize((150,150))
    img_obj = ImageTk.PhotoImage(resized_img)
    b1=Button(Boleta,text= x, image=img_obj, command= lambda : setCandidato(x["nombreC"]))
    b1.image= img_obj
    Boleta.pack(side="left",fill=None,expand=True, padx=5)
    nombrePart.pack()
    b1.pack()
    nombreCand.pack()

def mostrarCandidatos(localidad):
    collection = db.candidatos
    myquery = { "localidad": localidad }
    candidatos = collection.find(myquery)

    for x in candidatos:
        x["cantVotos"] = 0
        crearBotonCandidato(x)

def elegirCamara():
    variable = IntVar(app)
    variable.set(0)
    global fotoNoSacada

    borrarPantalla()
    def c():
        global fotoNoSacada
        cam = cv2.VideoCapture(variable.get())
        fotoNoSacada = True
        ingresarFoto(cam)
    
    fotoNoSacada = False
    choices = camarasDisponibles()

    w = OptionMenu(app, variable, *choices)
    w.pack()

    Button(app, text="Aceptar", command= c).pack()

def ingresarFoto(cam):
    global fotoNoSacada

    borrarPantalla()
  

    image_label = Label(app, height= 360, width= 640)
    botonFoto=Button(app,bg='green',fg='white',activebackground='white',activeforeground='green',text='Sacar Foto 📷',height=5,width=15,command=lambda:sacarFotoYComparar(cam))
    
    image_label.pack(pady= 20)
    
    botonFoto.pack(fill=None, expand=False)
    try:
        while fotoNoSacada:
            img=cam.read()[1]
            img1=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
            img= ImageTk.PhotoImage(Image.fromarray(img1))
            image_label['image']=img
            app.update()
    except:
        elegirCamara()
        mostrarMensaje(True, "Hubo un error con la camara intente con otra")
    

def ingresarDni():
    
    borrarPantalla()
    def actDni():
        global dni
        global esAdmin
        global cam

        dni = int(entryDni.get())
        if getValorDeUsuario(dni,"foto") != None:
            esAdmin = getValorDeUsuario(dni,"admin")
            if esAdmin:
                ingresarFoto(cam)
            else:
                if not(getValorDeUsuario(dni,"estadoVoto")):
                    ingresarFoto(cam)
                else:
                    mostrarMensaje(True, "Ya se ha registrado un voto con ese DNI")
        else:
            mostrarMensaje(True, "El dni no fue encontrado en el padron")
    labelDni = Label(app,text="Ingrese el dni").pack(pady=20)
    entryDni = Entry(app)
    entryDni.pack()
    botonFoto=Button(app,bg='green',fg='white',activebackground='white',activeforeground='green',text='Ingresar',height=3,width=15,command=actDni,)
    botonFoto.pack(fill=None, pady=20)

botonConfVoto = Button(app,bg='gray',fg='white',activebackground='white',activeforeground='green',text='Elije un candidato',height=5,width=15,command=votarCandidato)
sf = ScrolledFrame(app, width=640, height=210)
labelTitulo = Label(app, text="MiVoto", bg= "#05deff", fg= "white",name="titulo", height=1, font="Fixedsys 25").pack(pady=0,expand= False, fill= X, side="top")

sf.bind_arrow_keys(app)
sf.bind_scroll_wheel(app)
scroll = sf.display_widget(Frame)

ingresarDni()

#ingresarCandidato("Juntos por el Cambio","Jorge Macri","CABA","Es el primo de macri","https://www.lanacion.com.ar/resizer/3Q-QqSwmaLzE10MMg3dMxY3PHwU=/420x280/filters:format(webp):quality(70)/cloudfront-us-east-1.images.arcpublishing.com/lanacionar/UVSJ4WZ625HRLMSNO64W62U2YE.JPG")
#ingresarCandidato("Union por la Patria","Sergio Massa","Pais","Fundir el pais","https://pbs.twimg.com/profile_images/1639607611036188675/ER1KQEWf_400x400.jpg")
#ingresarCandidato("La Libertad Avanza", "Javier Milei", "Pais","Peinado crazy, el unico que sabe de economia","https://www.clarin.com/img/2023/09/06/X9spJoyJf_360x240__1.jpg")
app.mainloop()