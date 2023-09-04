import face_recognition
import urllib.request
from pymongo import MongoClient
import cv2
import customtkinter
from PIL import Image

app = customtkinter.CTk()
app.geometry("700x600")

connection_string = "mongodb+srv://mivotoapi:mivotoapi123@mivoto.n4q9rmw.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)
db = client.MiVoto

def ingresarPersona(dni, fotoUrl, estadoVoto):
    document = {"dni": dni, "foto": fotoUrl, "estadoVoto": estadoVoto} 

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

def sacarFoto(cam):
    cam_port = cam
    cam = cv2.VideoCapture(cam_port)

    result, image = cam.read()
    
    if result:
        resize = cv2.resize(image, (1920, 1080))
        cv2.imwrite("retratoCam.jpg", resize)
    else:
        print("No image detected. Please! try again")

def getImgUrlporDNI(dni):
    try:
        collection = db.usuario
        myquery = { "dni": dni }
        resp = collection.find(myquery)
        return resp[0]["foto"]
    except:
        print("An exception occurred 1")

dni = 46961189
fotoUrl = "https://i.imgur.com/XFi08aI.jpg"
estadoVoto = False



try:
    dni = int(input("Ingrese su DNI:\n- "))
    fotoUrl = getImgUrlporDNI(dni)
    if fotoUrl != None:
        #sacarFoto(1)
        imgPorLink(fotoUrl)
        if(compararCarasFotos("retratoCam.jpg", "retratoUrl.jpg")):
            print("Identidad verificada")
    else:
        print("DNI no encontrado en el padron")
    
    #ingresarPersona(dni, fotoUrl, estadoVoto)
    
    
    my_image = customtkinter.CTkImage(light_image=Image.open("retratoCam.jpg"), dark_image=Image.open("retratoCam.jpg"), size=(640, 360))
    image_label = customtkinter.CTkLabel(app, image=my_image, text="")
    image_label.pack()
except:
    print("ocurrio un error")

app.mainloop()