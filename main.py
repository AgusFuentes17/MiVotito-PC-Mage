import face_recognition
import urllib.request
from pymongo import MongoClient
import cv2
from tkinter import *
from PIL import Image, ImageTk
import time

app = Tk()
app.geometry("700x600")

connection_string = "mongodb+srv://mivotoapi:mivotoapi123@mivoto.n4q9rmw.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)
db = client.MiVoto

cam = cv2.VideoCapture(1)

fotoNoSacada = True
dniNoIngresado = True
def borrarPantalla():
    for widget in app.winfo_children():
        widget.pack_forget()

def votar():
    borrarPantalla()

def mostrarMensaje(malo, msg):
	if malo:
		mensaje = Label(app, text = msg, text_color='red')
	else:
		mensaje = Label(app, text = msg, text_color='green')
	mensaje.pack(pady= (10,0))
	app.update()
	time.sleep(2)
	mensaje.pack_forget()

def ingresarCandidato(nombreP, nombreC, localidad, politicas):
    document = {"nombreP": nombreP, "nombreC": nombreC, "localidad": localidad, "politicas":politicas, "cantVotos": 0} 
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

def imgPorLink(link):
    urllib.request.urlretrieve(link, "retratoUrl.jpg")

def compararCarasFotos(img1, img2):
    known_image = face_recognition.load_image_file(img1)
    image = face_recognition.load_image_file(img2)

    known_encoding = face_recognition.face_encodings(known_image)[0]
    unknown_encoding = face_recognition.face_encodings(image)[0]

    return face_recognition.compare_faces([known_encoding], unknown_encoding)

def sacarFotoYComparar():
    global fotoNoSacada
    result, image = cam.read()
    if result:
        resize = cv2.resize(image, (1920, 1080))
        cv2.imwrite("retratoCam.jpg", resize)
        imgPorLink(getImgUrlporDNI(dni))
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

dni = 46961189
fotoUrl = "https://i.imgur.com/XFi08aI.jpg"
estadoVoto = False

def getCandidatosXLocalidad(loca):
    listaC=[]
    collection = db.usuario
    myquery = { "localidad": loca }
    listaC = collection.find(myquery)
    for documento in listaC:
        documento["cantVotos"] = 0
    return listaC

def ingresarFoto():
    image_label = Label(app)
    botonFoto=Button(app,bg='green',fg='white',activebackground='white',activeforeground='green',text='Sacar Foto 📷',height=20,width=30,command=sacarFotoYComparar)

    borrarPantalla()
    image_label.pack()
    botonFoto.pack()
    while fotoNoSacada:
        img=cam.read()[1]
        img1=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        img= ImageTk.PhotoImage(Image.fromarray(img1))
        image_label['image']=img
        app.update()
    
    votar()

def ingresarDni():
    borrarPantalla()
    global dniNoIngresado
    def actDni():
        global dni
        global dniNoIngresado
        dni = int(entryDni.get())
        print(dni)
        dniNoIngresado = False
        ingresarFoto()

    entryDni = Entry(app)
    entryDni.pack()
    botonFoto=Button(app,bg='green',fg='white',activebackground='white',activeforeground='green',text='Ingresar',height=3,width=15,command=actDni,)
    botonFoto.pack()


ingresarDni()
app.mainloop()