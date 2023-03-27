#Importing Modules
from flask import Flask, render_template, request, redirect
import psycopg2
from keras.utils import load_img, img_to_array
from keras.models import load_model
import numpy as np
import os
import base64
from io import BytesIO
from PIL import Image
import smtplib
from email.message import EmailMessage
import datetime
import re
import hashlib
import imghdr


#intializing the flask app
app  = Flask('Soil_Identifier')


soilID = 0
User = "defaultuser"
loggedin = False
predicted = False
userid = 1
current_date = datetime.date.today()

#connecting to the database
mydb = psycopg2.connect(
    host=os.environ.get('DATABASE_HOST'),
    port=os.environ.get('DATABASE_PORT'),
    user=os.environ.get('DATABASE_USER'),
    password=os.environ.get('DATABASE_PASSWORD'),
    database=os.environ.get('DATABASE_NAME')
)

#Class of soil
classes = ["Black Soil","Laterite Soil","Peat Soil","Yellow Soil"]

#Loading trained model
model = load_model("SoilTypeIdentify.h5")


#Function to predict the soil type
def predict(file):
    # Preprocessing the image
    image = load_img(file, target_size=(220, 220)) #Resizing
    image = img_to_array(image) #image to array
    image = np.reshape(image,[1,220,220,3]) #reshaping according to the reqiuired dimensions
    image = (image/255.) #Rescaling
    
    # Predicting
    preds = model.predict(image) #return array with probabilities for each class
    predsLabel = np.argmax(preds) #return the class with highest probability
    
    # Inserting into the database
    mycursor = mydb.cursor()
    mycursor.execute("INSERT INTO login_history (\"user_ID\", \"soil_ID\", \"history_date\") VALUES (%s, %s, %s)", (userid, soilID, current_date))
    mydb.commit()

    # Converting probabilities in to percentages
    num0 = (preds[0][0])*100 #black percentage
    num1 = (preds[0][1])*100 #laterite percentage
    num2 = (preds[0][2])*100 #peat percentage
    num3 = (preds[0][3])*100 #yellow percentage
    
    # Rounding to two decimal places
    num0 = round(num0, 2)
    num1 = round(num1, 2)
    num2 = round(num2, 2)
    num3 = round(num3, 2)
    
    prediction = classes[predsLabel] #predicted class
    
    # Closing the database connection
    mydb.close()

    # Return predicted class and percentages as a tuple
    return prediction, num0, num1, num2, num3


#Setting starting app route
@app.route("/", methods=['GET', 'POST'])
def main():
	return render_template("login.html")


#Setting home page app route
@app.route("/home.html", methods=['GET', 'POST'])
def toHome():
    if loggedin:
        return render_template("home.html")
    else:
        return render_template("login.html")


#Setting reccomendation page app route
@app.route("/Recommendation.html", methods=['GET', 'POST'])
def recommend():
    if loggedin:
        return render_template("Recommendation.html")
    else:
        return render_template("login.html")


#Setting prediction page app route
@app.route("/predict.html", methods=['GET', 'POST'])
def predicting():
    if loggedin:
        return render_template("predict.html") 
    else:
        return render_template("login.html")	


#Setting submit page app route
@app.route("/submit", methods = ['GET', 'POST'])
def get_output():
    if request.method == 'POST':
        #Request user uploaded image
        img = request.files["my_image"]

        # Check if the file is an image
        if not imghdr.what(img) in {'png', 'jpeg', 'jpg', 'jfif'}:
            return render_template("predict.html", warn = "Invalid file type. Please upload a PNG, JPEG, JPG or JFIF image.")

        #Set path to save image
        #img_path1 = r"C:\Users\dell\Documents\SS-Website\static\img"
        img_path2 = img.filename
        stat_dir = r"\static\img" #Flask static directory

        #Path to save image
        img_path = os.path.join(stat_dir+"\\"+img_path2)    
        img.save(img_path)

        #Predicting the given image
        results = predict(img_path)

        #New saved image in the static directory
        img_path = os.path.join(stat_dir+"\\"+img_path2)

        #Predicted results
        prediction = (results[0]) # Predicted soil type
        blackPercentage = ("{:.2f}".format(results[1])+" %") #Black percentage
        lateralPercentage = ("{:.2f}".format(results[2])+" %") #Laterite percentage
        peatPercentage = ("{:.2f}".format(results[3])+" %") #Peat percentage
        yellowPercentage = ("{:.2f}".format(results[4])+" %") #Yellow percentage

    return render_template("predict.html", prediction=prediction, img_path=img_path, 
                           blackPercentage=blackPercentage, lateralPercentage=lateralPercentage, 
                           peatPercentage=peatPercentage, yellowPercentage=yellowPercentage)


#Setting AboutUs page app route
@app.route("/AboutUs.html", methods=['GET', 'POST'])
def about():
    if loggedin:
        return render_template("AboutUs.html") 
    else:
        return render_template("login.html")	


#Setting login page app route
@app.route("/login.html", methods=['GET', 'POST'])
def logIn():
	return render_template("login.html")


#Check login with database
# Login function
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Hash the password
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # Establishing connection to the database
    mydb = mysql.connector.connect(
        host="localhost",
        user="yourusername",
        password="yourpassword",
        database="yourdatabase"
    )

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM users WHERE \"username\" = %s AND \"password\" = %s", (username, password_hash))

    user = mycursor.fetchone()

    if user:
        global loggedin
        loggedin = True 
        mycursor.execute("SELECT \"user_ID\" FROM \"users\" WHERE \"username\" = %s", (username,))
        result = mycursor.fetchone()
        global userid
        userid = result[0]
        print(userid)
        # Closing the database connection
        mydb.close()
        return render_template("home.html")
    else:
        # Closing the database connection
        mydb.close()
        return render_template("login.html", message1="Login unsuccessful!!!", message2="Wrong username and or Password!!!")

# #Setting signup page app route
# @app.route("/signup.html", methods=['GET', 'POST'])
# def signIn():
# 	return render_template("signup.html")

#checks if the user exists if not allows sign up
# Signup function
@app.route('/signup', methods=['POST'])
def signup_post():
    username = request.form['sUsername']
    password = request.form['sPassword']

    # Hash the password
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # Password validation
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%^&+=]).{8,}$', password):
        return render_template("login.html", message3="Password should be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character")

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM users WHERE \"username\" = %s", (username,))
    existing_user = mycursor.fetchone()
    if existing_user:
        mycursor.close()
        return render_template("login.html", message3="Username already exists")
    else:
        mycursor.execute("INSERT INTO users (\"username\", \"password\") VALUES (%s, %s)", (username, password_hash))

        mydb.commit()
        mycursor.close()
        return render_template("login.html", message3="Account Created Successfully!!!")




#Setting contact page app route
@app.route("/contact.html", methods=['GET', 'POST'])
def contactUs():
    if loggedin:
        if request.method == 'POST':
            # Get form data
            name = request.form['name']
            email = request.form['email']
            message = request.form['message']
            subject = request.form['subject']

            # Create email message
            msg = EmailMessage()
            msg['Subject'] = 'New contact form submission from ' + name
            msg['From'] = email
            msg['To'] = 'soilstation.se32@gmail.com' 
            msg.set_content('Name: ' + name + '\n\nEmail: ' + email + '\n\nSubject: ' + subject + '\n\nMessage: ' + message)

            # Send email
            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.starttls()
                    smtp.login('soilstation.se32@gmail.com', 'izjuhdugrmobvfiw') 
                    smtp.send_message(msg)
            except (smtplib.SMTPException, smtplib.SMTPAuthenticationError) as e:
                print('Error occurred while sending email:', str(e))
                return "Error occurred while sending email. Please try again later."

            return render_template("contact.html", message="Your message has been sent. Thank you!")

        # If request.method is GET, render the contact form
        return render_template("contact.html")
    else:
        return render_template("login.html")



#Setting contact page app route
@app.route("/history.html", methods=['GET', 'POST'])
def checkHistory():
    if loggedin:
        # perform a SQL query to retrieve the relevant data
        mycursor = mydb.cursor()
        mycursor.execute("SELECT \"soil_types\".\"soil_ID\", \"soil_types\".\"Soil_Type\", \"login_history\".\"history_date\" FROM \"login_history\" JOIN \"soil_types\" ON \"login_history\".\"soil_ID\" = \"soil_types\".\"soil_ID\" WHERE \"login_history\".\"user_ID\" = %s",(userid,))
        rows = mycursor.fetchall()
        # if there are no records, display a message instead of the table
        if not rows:
            mycursor.close()
            return render_template('history.html', msg = "No History records found for this user ")
        # pass the data to the Jinja template to render the table
        mycursor.close()
        return render_template('history.html', rows=rows)
    else:
        return render_template("login.html")


#Setting plant recommendation page app route
@app.route("/plants.html", methods=['GET', 'POST'])
def plantRecommend():
    if loggedin:
        if predicted:
            mycursor = mydb.cursor()
            mycursor.execute('SELECT "Plant_Name", "Image", "Description", "Treatment_Methods" FROM "plants" WHERE "Soil_ID" = %s', (soilID,))
            plants = mycursor.fetchall()

            # Convert BLOB images to PNG format and base64-encoded data URIs
            new_plants = []
            for plant in plants:
                img = Image.open(BytesIO(plant[1]))
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                img_data_uri = f"data:image/png;base64,{img_str}"
                new_plants.append((plant[0], img_data_uri, plant[2], plant[3]))

            mycursor.close()
            return render_template('plants.html', plants=new_plants)
        else:
            return render_template("predict.html")
    else:
        return render_template("login.html")

    

@app.route("/signout.html", methods= ["GET"])
def signingout():
    global loggedin
    if loggedin:
        loggedin = False
        return render_template("login.html")
    else:
        return render_template("login.html")


@app.route("/black.html", methods= ["GET"])
def getBlack():
    global soilID
    global predicted
    if loggedin:
        soilID = 1
        predicted = True
        return redirect("/plants.html")
    else:
        return render_template("login.html")

  
@app.route("/laterite.html", methods= ["GET"])
def getLaterite():
    global soilID
    global predicted
    if loggedin:
        soilID = 2
        predicted = True
        return redirect("/plants.html")
    else:
        return render_template("login.html")


@app.route("/peat.html", methods= ["GET"])
def getPeat():
    global soilID
    global predicted
    if loggedin:
        soilID = 3
        predicted = True
        return redirect("/plants.html")
    else:
        return render_template("login.html")


@app.route("/yellow.html", methods= ["GET"])
def getYellow():
    global soilID
    global predicted
    if loggedin:
        soilID = 4
        predicted = True
        return redirect("/plants.html")
    else:
        return render_template("login.html")


#Running the app
if __name__ =='__main__':
	#app.debug = True
	app.run(debug = True)