import face_recognition
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

cam = cv2.VideoCapture(1)


fotoNoSacada = True
dniNoIngresado = True

candidato = ""
dni = None
fotoUrl = "https://i.imgur.com/XFi08aI.jpg"
estadoVoto = False

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
        if widget["text"] != "MiVoto 2023":
            widget.pack_forget()
    for widget in scroll.winfo_children():
        widget.pack_forget()

def votarPresidente():

    global botonConfVoto
    borrarPantalla()

    titulo = Label(app, text="Candidatos a Presidente")
    titulo.pack(pady=10)
    sf.pack(side="top", expand=0, fill=None)

    mostrarCandidatos("Pais")
    botonConfVoto.pack(fill=None,pady=10)

def votarGobernador():
    global botonConfVoto
    global dni

    borrarPantalla()

    titulo = Label(app, text="Candidatos a Gobernador")
    titulo.pack(pady=10)
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

    if noVoto(dni):
        newvalues = { "$set": { "estadoVoto": True } }
        collection = db.usuario
        collection.update_one(myquery, newvalues)
        votarGobernador()
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

def ingresarCandidato(nombreP, nombreC, localidad, politicas, imgLink):
    document = {"nombreP": nombreP, "nombreC": nombreC, "localidad": localidad, "politicas":politicas,"imgLink": imgLink, "cantVotos": 0} 
    try:
        collection = db.candidatos
        collection.insert_one(document)
    except:
        print("ocurrio un error")

def ingresarPersona(dni, fotoUrl):
    document = {"dni": dni, "foto": fotoUrl, "estadoVoto": False} 
    try:
        collection = db.usuario
        collection.insert_one(document)
    except:
        print("ocurrio un error")        

def imgPorLink(link,nombre):
    urllib.request.urlretrieve(link, nombre)

def compararCarasFotos(img1, img2):
    known_image = face_recognition.load_image_file(img1)
    image = face_recognition.load_image_file(img2)

    known_encoding = face_recognition.face_encodings(known_image)[0]
    unknown_encoding = face_recognition.face_encodings(image)[0]

    return face_recognition.compare_faces([known_encoding], unknown_encoding)

def noVoto(dni):
    try:
        collection = db.usuario
        myquery = { "dni": dni }
        resp = collection.find(myquery)
        return not(resp[0]["estadoVoto"])
    except:
        return None

def sacarFotoYComparar():
    global fotoNoSacada
    result, image = cam.read()
    if result:
        resize = cv2.resize(image, (1920, 1080))
        cv2.imwrite("retratoCam.jpg", resize)
        imgPorLink(getImgUrlporDNI(dni),"retratoUrl.jpg")
        if compararCarasFotos("retratoCam.jpg","retratoUrl.jpg"):
            fotoNoSacada = False
        else:
            mostrarMensaje(True, "No se logro confirmar su identidad. Vuelva a sacar la foto")
    else:
        mostrarMensaje(True, "No se logro confirmar su identidad. Vuelva a sacar la foto")

def getImgUrlporDNI(dni):
    try:
        collection = db.usuario
        myquery = { "dni": dni }
        resp = collection.find(myquery)
        return resp[0]["foto"]
    except:
        return None

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

def ingresarFoto():
    image_label = Label(app)
    botonFoto=Button(app,bg='green',fg='white',activebackground='white',activeforeground='green',text='Sacar Foto 📷',height=20,width=30,command=sacarFotoYComparar)

    borrarPantalla()
    image_label.pack()
    botonFoto.pack(fill=None)
    while fotoNoSacada:
        img=cam.read()[1]
        img1=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        img= ImageTk.PhotoImage(Image.fromarray(img1))
        image_label['image']=img
        app.update()
    
    votarPresidente()

def ingresarDni():
    borrarPantalla()
    def actDni():
        global dni
        dni = int(entryDni.get())
        if getImgUrlporDNI(dni) != None:
            if noVoto(dni):  
                ingresarFoto()
            else:
                mostrarMensaje(True, "Ya se ha registrado un voto con ese DNI")
        else:
            mostrarMensaje(True, "El dni no fue encontrado en el padron")

    entryDni = Entry(app)
    entryDni.pack()
    botonFoto=Button(app,bg='green',fg='white',activebackground='white',activeforeground='green',text='Ingresar',height=3,width=15,command=actDni,)
    botonFoto.pack(fill=None)

botonConfVoto = Button(app,bg='gray',fg='white',activebackground='white',activeforeground='green',text='Elije un candidato',height=5,width=15,command=votarCandidato)
sf = ScrolledFrame(app, width=640, height=210)

sf.bind_arrow_keys(app)
sf.bind_scroll_wheel(app)
scroll = sf.display_widget(Frame)

ingresarDni()

#ingresarCandidato("Juntos por el Cambio","Jorge Macri","CABA","Es el primo de macri","https://www.lanacion.com.ar/resizer/3Q-QqSwmaLzE10MMg3dMxY3PHwU=/420x280/filters:format(webp):quality(70)/cloudfront-us-east-1.images.arcpublishing.com/lanacionar/UVSJ4WZ625HRLMSNO64W62U2YE.JPG")
#ingresarCandidato("Union por la Patria","Sergio Massa","Pais","Fundir el pais","https://pbs.twimg.com/profile_images/1639607611036188675/ER1KQEWf_400x400.jpg")
#ingresarCandidato("La Libertad Avanza", "Javier Milei", "Pais","Peinado crazy, el unico que sabe de economia","https://www.clarin.com/img/2023/09/06/X9spJoyJf_360x240__1.jpg")
app.mainloop()