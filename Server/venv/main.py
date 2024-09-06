import pymongo
import speech_recognition as sr
import pyttsx3
import datetime
import requests
import re
import bcrypt
from PIL import Image
import matplotlib.pyplot as plt
from io import BytesIO
import random
import smtplib
from email.mime.text import MIMEText


# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['user_database']
users_collection = db['users']
orders_collection = db['orders']

# Initialize recognizer and text-to-speech engine
listener = sr.Recognizer()
engine = pyttsx3.init()

# Function to convert text to speech
def talk(text):
    engine.say(text)
    engine.runAndWait()


def generate_verification_code():
    return str(random.randint(100000, 999999))

def send_verification_code(email, code):
    sender = "your_email@example.com"
    password = "your_email_password"
    subject = "Your Verification Code"
    body = f"Your verification code is: {code}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = email

    with smtplib.SMTP_SSL("smtp.example.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, email, msg.as_string())

    talk("A verification code has been sent to your email.")

def verify_code(input_code, actual_code):
    return input_code == actual_code

# Function to get user input through the microphone with validation
def get_info(prompt):
    while True:
        try:
            with sr.Microphone() as source:
                print(prompt)
                talk(prompt)
                voice = listener.listen(source)
                info = listener.recognize_google(voice)
                print(info)
                if info.strip() != "":
                    return info.lower()
                else:
                    talk("Sorry, I didn't catch that. Please try again.")
        except sr.UnknownValueError:
            talk("Sorry, I did not understand that. Please try again.")
        except sr.RequestError:
            talk("Sorry, my speech service is down.")

# Function to handle searching for a product
def search_product():
    talk('What product are you looking for?')
    product_name = get_info('What product are you looking for?')

    # Ask for filters
    talk('Do you want to apply any filters? You can say "price range", "category", or "ratings". Say "no filters" to skip.')
    filter_choice = get_info('Do you want to apply any filters? You can say "price range", "category", or "ratings". Say "no filters" to skip.')
    
    filters = {}
    
    if 'price range' in filter_choice:
        talk('What is the minimum price?')
        min_price = float(get_info('What is the minimum price?'))
        talk('What is the maximum price?')
        max_price = float(get_info('What is the maximum price?'))
        filters['price'] = {'$gte': min_price, '$lte': max_price}
        
    if 'category' in filter_choice:
        talk('Which category are you interested in?')
        category = get_info('Which category are you interested in?')
        filters['category'] = category
    
    if 'ratings' in filter_choice:
        talk('What is the minimum rating?')
        min_rating = float(get_info('What is the minimum rating?'))
        filters['rating'] = {'$gte': min_rating}
    
    # Call the Fake Store API to fetch products
    query_params = {'limit': 5, 'q': product_name}
    response = requests.get('https://fakestoreapi.com/products', params=query_params)
    products = response.json()
    
    # Apply filters
    filtered_products = []
    for product in products:
        if 'price' in filters:
            if not (filters['price']['$gte'] <= product['price'] <= filters['price']['$lte']):
                continue
        if 'category' in filters:
            if product['category'] != filters['category']:
                continue
        if 'rating' in filters:
            if product['rating']['rate'] < filters['rating']['$gte']:
                continue
        filtered_products.append(product)
    
    if filtered_products:
        talk(f'Showing results for {product_name} with applied filters.')
        for product in filtered_products:
            talk(product['description'])
            image_url = product['image']
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            plt.imshow(img)
            plt.axis('off')
            plt.show()
            talk('Do you want to add this product to your cart?')
            add_to_cart = get_info('Do you want to add this product to your cart?')
            if 'yes' in add_to_cart:
                cart.append(product)
                talk(f'Added {product["title"]} to your cart.')
            talk('Do you want to hear the next result?')
            next_result = get_info('Do you want to hear the next result?')
            if 'no' in next_result:
                break
    else:
        talk('No products found matching your search and filters.')
    
    talk('End of search results.')


# Function to check if a product is eligible for return
def check_eligibility(order_number, product_name):
    # Find the order in the database
    order = orders_collection.find_one({'order_number': order_number})
    
    if order:
        # Check if the product is in the order
        if product_name in order['products']:
            # Calculate the days since purchase
            purchase_date = order['purchase_date']
            days_since_purchase = (datetime.datetime.now() - purchase_date).days
            
            # Check if the product is eligible for return
            if days_since_purchase <= 7 and order['category'] == 'eligible_category':  # Assuming 'eligible_category' is the category that can be returned
                return True
            else:
                talk('Sorry, the product is not eligible for return.')
                return False
        else:
            talk('Product not found in the order.')
            return False
    else:
        talk('Order not found.')
        return False

# Function to handle reporting a product issue
def report_issue():
    talk('Please describe the issue you are facing with the product or you want to return the product?')
    issue_description = get_info('Please describe the issue you are facing with the product or you want to return the product?')
    print(f'Reported issue: {issue_description}')
    if 'return the product' in issue_description:
        # Initiate returning process
        talk('Could you please provide your order number?')
        order_number = get_info('Could you please provide your order number?')
        talk('Which product from the order you want to return?')
        product_name = get_info('Which product from the order you want to return?')
        talk('What is the reason for returning the product?')
        reason = get_info('What is the reason for returning the product?')
        
        # Check if the product is eligible for return
        if check_eligibility(order_number, product_name):
            talk('Your product is eligible for return. We would initiate the refund quickly.')
        else:
            talk('Sorry, the product is not eligible for return.')
        
        talk('Would you like any further assistance?')
        user_response = get_info('Would you like any further assistance?')
        if 'no' in user_response:
            talk('Okay, Thanks. Have a great day!')
        else:
            talk('How can I help you?')
            user_voice = get_info('How can I help you?')
            # React accordingly
    else:
        talk('Thank you for reporting the issue. We will look into it.')

# Function to handle viewing the cart
def view_cart():
    if cart:
        talk('Your cart contains the following items:')
        for item in cart:
            talk(item['title'])
    else:
        talk('Your cart is empty.')

# Function to handle placing an order
def place_order():
    if cart:
        talk('Placing your order...')
        order_number = f'ORD{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        order = {
            'order_number': order_number,
            'purchase_date': datetime.datetime.now(),
            'products': [item['title'] for item in cart],
            'user_email': logged_in_user['email'],
            'status': 'Processing'  # Add status field
        }
        orders_collection.insert_one(order)
        talk(f'Order placed successfully! Your order number is {order_number}.')
        cart.clear()  # Clear the cart after placing the order
    else:
        talk('Your cart is empty.')

def update_order_status(order_number, new_status):
    orders_collection.update_one(
        {'order_number': order_number},
        {'$set': {'status': new_status}}
    )
    talk(f'Order {order_number} status updated to {new_status}.')

def track_order():
    talk('Please provide your order number.')
    order_number = get_info('Please provide your order number.')
    
    # Find the order in the database
    order = orders_collection.find_one({'order_number': order_number, 'user_email': logged_in_user['email']})
    
    if order:
        talk(f'Your order status is: {order["status"]}.')
    else:
        talk('Order not found or you do not have permission to track this order.')

# Function to view orders
def view_orders():
    orders = orders_collection.find({'user_email': logged_in_user['email']})
    if orders.count() > 0:
        talk('Your orders are:')
        for order in orders:
            talk(f"Order number: {order['order_number']}, Products: {', '.join(order['products'])}, Date: {order['purchase_date']}")
    else:
        talk('You have no orders.')

# Function to handle adding a product to the wishlist
def add_to_wishlist(product):
    if logged_in_user:
        user_email = logged_in_user['email']
        users_collection.update_one(
            {'email': user_email},
            {'$addToSet': {'wishlist': product}}
        )
        talk(f'Added {product["title"]} to your wishlist.')
    else:
        talk('You need to be logged in to add items to your wishlist.')

# Function to handle viewing the wishlist
def view_wishlist():
    if logged_in_user:
        user_email = logged_in_user['email']
        user = users_collection.find_one({'email': user_email})
        wishlist = user.get('wishlist', [])
        if wishlist:
            talk('Your wishlist contains the following items:')
            for item in wishlist:
                talk(item['title'])
        else:
            talk('Your wishlist is empty.')
    else:
        talk('You need to be logged in to view your wishlist.')
        
def help_command():
    commands = [
        'search for a product',
        'view cart',
        'place order',
        'view orders',
        'track order',
        'view wishlist',
        'report a product issue',
        'help'
    ]
    talk('Here are the commands you can use:')
    for command in commands:
        talk(command)

def update_name():
    talk('What would you like to update your name to?')
    new_name = get_info('Please provide your new name.')
    users_collection.update_one({'email': logged_in_user['email']}, {'$set': {'name': new_name}})
    logged_in_user['name'] = new_name
    talk('Your name has been updated successfully.')

def update_email():
    while True:
        talk('What would you like to update your email to?')
        new_email = get_info('Please provide your new email.')
        if validate_email(new_email):
            # Check if the new email already exists
            existing_user = users_collection.find_one({'email': new_email})
            if existing_user:
                talk('This email is already associated with another account. Please try a different email.')
            else:
                break
        else:
            talk("Sorry, that's not a valid email address. Please try again.")
    users_collection.update_one({'email': logged_in_user['email']}, {'$set': {'email': new_email}})
    logged_in_user['email'] = new_email
    talk('Your email has been updated successfully.')

def update_password():
    talk('What would you like to update your password to?')
    new_password = get_info('Please provide your new password.')
    hashed_password = hash_password(new_password)
    users_collection.update_one({'email': logged_in_user['email']}, {'$set': {'password': hashed_password}})
    talk('Your password has been updated successfully.')



def update_profile():
    while True:
        talk('What would you like to update? You can say "name", "email", or "password".')
        choice = get_info('What would you like to update? You can say "name", "email", or "password".')
        if 'name' in choice:
            update_name()
            break
        elif 'email' in choice:
            update_email()
            break
        elif 'password' in choice:
            update_password()
            break
        else:
            talk("Sorry, I did not understand that. Please try again.")


def fetch_order_history(email):
    orders = orders_collection.find({'user_email': email})
    return list(orders)

def display_order_details(order):
    talk(f"Order number: {order['order_number']}")
    talk(f"Purchase date: {order['purchase_date']}")
    talk(f"Status: {order['status']}")
    talk("Products in this order:")
    for product in order['products']:
        talk(product)

def view_order_history():
    orders = fetch_order_history(logged_in_user['email'])
    if orders:
        talk('Here is your order history:')
        for order in orders:
            display_order_details(order)
            talk('Do you want to hear details for the next order?')
            next_order = get_info('Do you want to hear details for the next order?')
            if 'no' in next_order:
                break
    else:
        talk('You have no orders in your history.')


# Example schema for promotions
promotions_collection = db['promotions']

# Sample data structure for promotions
promotions = [
    {
        "promotion_id": "promo_001",
        "title": "Summer Sale",
        "description": "Get 20% off on all summer items.",
        "category": "summer",
        "start_date": datetime.datetime(2024, 8, 1),
        "end_date": datetime.datetime(2024, 8, 31)
    },
    {
        "promotion_id": "promo_002",
        "title": "Back to School",
        "description": "Save 15% on school supplies.",
        "category": "school",
        "start_date": datetime.datetime(2024, 8, 1),
        "end_date": datetime.datetime(2024, 8, 15)
    }
]

# Insert sample data into the database
promotions_collection.insert_many(promotions)

def update_user_interests(user_email, interests):
    users_collection.update_one({'email': user_email}, {'$set': {'interests': interests}})

def notify_promotions(user):
    interests = user.get('interests', [])
    if not interests:
        talk('You have no specific interests listed. Please update your preferences to receive tailored promotions.')
        return

    # Fetch current promotions
    now = datetime.datetime.now()
    promotions = promotions_collection.find({
        'category': {'$in': interests},
        'start_date': {'$lte': now},
        'end_date': {'$gte': now}
    })

    if promotions.count() > 0:
        talk('Here are some promotions that might interest you:')
        for promo in promotions:
            talk(f"Promotion: {promo['title']}")
            talk(f"Description: {promo['description']}")
            talk(f"Valid from {promo['start_date'].strftime('%Y-%m-%d')} to {promo['end_date'].strftime('%Y-%m-%d')}.")
    else:
        talk('There are no current promotions matching your interests.')

# Modify the user_actions function to include wishlist options
def user_actions():
    while True:
        talk('What would you like to do next? You can say "search for a product", "view cart", "place order", "view orders", "track order", "view wishlist", "report a product issue", "update profile", "view order history", "check promotions", or "help".')
        action = get_info('What would you like to do next? You can say "search for a product", "view cart", "place order", "view orders", "track order", "view wishlist", "report a product issue", "update profile", "view order history", "check promotions", or "help".')
        if 'search' in action:
            search_product()
        elif 'view cart' in action:
            view_cart()
        elif 'place order' in action:
            place_order()
        elif 'view orders' in action:
            view_orders()
        elif 'track order' in action:
            track_order()
        elif 'view wishlist' in action:
            view_wishlist()
        elif 'report' in action:
            report_issue()
        elif 'update profile' in action:
            update_profile()
        elif 'view order history' in action:
            view_order_history()
        elif 'check promotions' in action:
            notify_promotions(logged_in_user)
        elif 'help' in action:
            help_command()
        else:
            talk("Sorry, I did not understand that. Please try again.")

# Function to hash password
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

# Function to check password
def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# Function to validate email address
def validate_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if re.match(pattern, email):
        return True
    else:
        return False

# Function to validate mobile number
def validate_mobile_number(mobile):
    pattern = r"^\d{10}$"
    if re.match(pattern, mobile):
        return True
    else:
        return False



def login():
    while True:
        talk('Please provide your email.')
        email = get_info('Please provide your email.')
        user = users_collection.find_one({'email': email})
        
        if user:
            talk('Please provide your password.')
            password = get_info('Please provide your password.')
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                verification_code = generate_verification_code()
                send_verification_code(email, verification_code)
                
                talk('Please enter the verification code sent to your email.')
                input_code = get_info('Please enter the verification code sent to your email.')
                if verify_code(input_code, verification_code):
                    global logged_in_user
                    logged_in_user = user
                    talk('Login successful.')
                    user_actions()
                    return
                else:
                    talk('Incorrect verification code. Please try again.')
            else:
                talk('Incorrect password. Please try again.')
        else:
            talk('No user found with this email. Please try again.')


# Function to get email info with validation
def get_email_info():
    global logged_in_user  # Use a global variable to keep track of the logged-in user
    talk('Hi Sir, I am your assistant for today. Do you want to create an account or login?')
    response = get_info('Please respond with "create an account" or "login"')
    
    if 'create an account' in response:
        talk('What is your name?')
        customer_name = get_info('Please tell me your name')
        print(customer_name)
        
        while True:
            talk('What is your email id?')
            customer_emailid = get_info('Please tell me your email id')
            print(customer_emailid)
            if validate_email(customer_emailid):
                break
            else:
                talk("Sorry, that's not a valid email. Please try again.")
            
            # Check if the email address already exists
            existing_user = users_collection.find_one({'email': customer_emailid})
            
            if existing_user:
                talk('Email address already exists. Please try again.')
            else:
                break
        
        while True:
            talk('What is your mobile number?')
            customer_mobile = get_info('Please tell me your mobile number')
            print(customer_mobile)
            if validate_mobile_number(customer_mobile):
                break
            else:
                talk("Sorry, that's not a valid mobile number. Please try again.")
                
            # Check if the mobile number already exists
            existing_user_mobile = users_collection.find_one({'mobileno': customer_mobile})
            
            if existing_user_mobile:
                talk('Mobile no. already exists. Please try again.')
            else:
                break
            
            #forgot password option
        
        talk('What is your password?')
        customer_password = get_info('Please tell me your password')
        print(customer_password)
        
        # Hash password
        hashed_password = hash_password(customer_password)
        
        # Save user info to MongoDB
        user = {
            'name': customer_name,
            'email': customer_emailid,
            'mobile': customer_mobile,
            'password': hashed_password
        }
        users_collection.insert_one(user)
        
        talk('Account created successfully!')
        logged_in_user = user  # Set the logged-in user
        login()  # Proceed to login after account creation
        
    elif 'login' in response:
        login()
    
    else:
        talk("Sorry, I did not catch that. Please try again.")
        get_email_info()

# Global variables for cart and logged-in user
cart = []
logged_in_user = None

# Start the interaction
# Your existing code here...

if __name__ == "__main__":
    get_email_info()  # This starts the interaction
