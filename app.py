from flask import Flask, render_template
from auth.login import auth_bp
from faculty.faculty_routes import faculty_bp

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(faculty_bp)

@app.route("/")
def home():
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)
