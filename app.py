from flask import Flask, render_template, request, redirect, url_for, session
import datetime, json, os
import re

app = Flask(__name__)

SYMPTOM_DB = {
    "fever": ("Take rest, stay hydrated, use paracetamol.", "Viral Infection or Flu", "General Physician"),
    "sore throat": ("Gargle with warm salt water, drink warm fluids.", "Throat Infection or Common Cold", "ENT Specialist"),
    "cough": ("Use cough syrup, inhale steam.", "Respiratory Infection", "Pulmonologist"),
    "headache": ("Rest in a quiet room, take painkillers if needed.", "Migraine or Tension Headache", "Neurologist"),
    "fatigue": ("Ensure good sleep, balanced diet, and hydration.", "Chronic Fatigue or Anemia", "General Physician"),
    "cold": ("Stay warm, drink fluids, use nasal decongestants.", "Common Cold", "General Physician"),
    "body aches": ("Use pain relievers, stay warm, rest.", "Flu or Viral Infection", "General Physician"),
    "runny nose": ("Use a saline nasal spray, stay hydrated.", "Allergic Rhinitis or Cold", "ENT Specialist"),
    "chills": ("Wear warm clothing, take warm liquids.", "Infection or Flu", "General Physician"),
    "nausea": ("Sip ginger tea or take anti-nausea medicine.", "Gastric Issue", "Gastroenterologist"),
    "vomiting": ("Stay hydrated, take antiemetic medication if needed.", "Food Poisoning or Stomach Flu", "Gastroenterologist"),
    "diarrhea": ("Stay hydrated, avoid dairy and high-fat foods.", "Gastrointestinal Infection", "Gastroenterologist"),
    "constipation": ("Eat fiber-rich foods, drink plenty of water.", "Digestive Problems", "Gastroenterologist"),
    "dizziness": ("Rest, stay hydrated, avoid sudden movements.", "Low Blood Pressure or Vertigo", "Neurologist"),
    "shortness of breath": ("Seek medical attention if severe; try slow, deep breathing.", "Asthma or Heart Issue", "Pulmonologist / Cardiologist"),
    "chest pain": ("Seek immediate medical attention, especially if it persists.", "Heart Problem", "Cardiologist"),
    "joint pain": ("Use pain relievers, rest, apply ice to reduce swelling.", "Arthritis", "Orthopedic Specialist"),
    "swelling": ("Apply ice or a cold compress, elevate the swollen area.", "Injury or Infection", "General Physician"),
    "rash": ("Avoid scratching, use anti-itch creams, stay cool.", "Skin Allergy", "Dermatologist"),
    "itchy skin": ("Use anti-itch creams or moisturizers.", "Dermatitis", "Dermatologist"),
    "abdominal pain": ("Rest, avoid heavy meals, use heat pads.", "Gastric Issue or Appendicitis", "Gastroenterologist"),
    "leg cramps": ("Stretch the muscle gently, stay hydrated.", "Muscle Fatigue", "Orthopedic Specialist"),
    "back pain": ("Rest, apply heat or cold compress, take pain relievers.", "Muscle Strain", "Orthopedic Specialist"),
    "numbness": ("Avoid pressure on affected area, rest.", "Nerve Compression", "Neurologist"),
    "blurry vision": ("Rest your eyes, take breaks, and consult a doctor if it persists.", "Eye Strain or Vision Problem", "Ophthalmologist"),
    "ringing in ears": ("Avoid loud environments, try relaxation techniques.", "Tinnitus", "ENT Specialist"),
    "insomnia": ("Try a sleep routine, limit caffeine, avoid screen time before bed.", "Sleep Disorder", "Psychiatrist / Sleep Specialist"),
    "dry mouth": ("Stay hydrated, use mouthwash, chew sugar-free gum.", "Dehydration or Diabetes", "General Physician"),
    "canker sores": ("Use soothing mouth rinses, avoid acidic foods.", "Mouth Ulcers", "Dentist"),
    "bloody nose": ("Pinch nostrils and lean forward, apply a cold compress.", "Nasal Irritation", "ENT Specialist"),
    "nosebleeds": ("Pinch nostrils, stay calm, and apply a cold compress.", "Nasal Dryness or Trauma", "ENT Specialist"),
    "pale skin": ("Ensure proper hydration and nutrition, avoid extreme heat.", "Anemia", "General Physician"),
    "weight loss": ("Consult a doctor, eat balanced meals, stay hydrated.", "Malnutrition or Thyroid Disorder", "Endocrinologist"),
    "weight gain": ("Monitor diet, engage in physical activity, stay hydrated.", "Obesity or Thyroid Problem", "Endocrinologist"),
    "anxiety": ("Practice relaxation techniques, deep breathing, or meditation.", "Anxiety Disorder", "Psychiatrist"),
    "depression": ("Seek professional help, maintain a routine, stay active.", "Depression", "Psychiatrist"),
    "food poisoning": ("Stay hydrated, avoid solid foods for a few hours.", "Bacterial or Viral Infection", "Gastroenterologist"),
    "stomachache": ("Rest, drink warm water, avoid heavy food.", "Gastritis or Infection", "Gastroenterologist"),
    "period cramps": ("Use heat pads, take pain relievers, avoid caffeine.", "Menstrual Pain", "Gynecologist")
}

def save_log(symptoms, username="guest"):
    with open("symptoms.txt", "a") as file:
        file.write(f"{datetime.datetime.now()} - {username}: {symptoms}\n")

    if os.path.exists("user_data.json") and os.path.getsize("user_data.json") > 0:
        try:
            with open("user_data.json", "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}

    if username not in data:
        data[username] = []

    data[username].append({"date": str(datetime.date.today()), "symptoms": symptoms})

    with open("user_data.json", "w") as f:
        json.dump(data, f, indent=4)

def get_user_trends(username="guest"):
    trends = {}
    if not os.path.exists("user_data.json") or os.path.getsize("user_data.json") == 0:
        return trends

    try:
        with open("user_data.json", "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return trends

    if username not in data:
        return trends

    for log in data[username]:
        for s in log["symptoms"].split(","):
            s = s.strip().lower()
            trends[s] = trends.get(s, 0) + 1

    return trends

def get_symptom_logs():
    logs = []
    if not os.path.exists("symptoms.txt"):
        return logs
    with open("symptoms.txt", "r") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            if ' - ' in line:
                timestamp, rest = line.split(' - ', 1)
                if ':' in rest:
                    username, symptoms = rest.split(':', 1)
                    logs.append({
                        "timestamp": timestamp.strip(),
                        "username": username.strip(),
                        "symptoms": symptoms.strip()
                    })
                else:
                    logs.append({
                        "timestamp": timestamp.strip(),
                        "username": "Unknown",
                        "symptoms": rest.strip()
                    })
    return logs

@app.route("/", methods=["GET", "POST"])
def index():
    output = {}
    if request.method == "POST":
        symptoms = request.form.get("symptoms")
        save_log_option = request.form.get("save_log")
        username = "guest"

        if not symptoms or not symptoms.strip():
            return render_template("index.html", error="❌ Please enter valid symptoms.")

        symptoms_cleaned = symptoms.lower()
        symptoms_cleaned = re.sub(r"\b(i have|i am|i'm|having|experiencing|suffering from|feeling|a|and)\b", '', symptoms_cleaned)
        symptoms_cleaned = re.sub(r'[^\w\s]', '', symptoms_cleaned)
        symptoms_cleaned = symptoms_cleaned.strip()

        matched = []
        for key_symptom in SYMPTOM_DB.keys():
            if re.search(r'\b' + re.escape(key_symptom) + r'\b', symptoms_cleaned):
                matched.append((key_symptom, SYMPTOM_DB[key_symptom]))

        if matched:
            output["issue"] = "🧠 Possible Issues: Common Cold or Viral Flu"
            output["suggestions"] = matched
            output["advice"] = "💡 Advice: If symptoms last more than 3 days, please consult a doctor."

            if save_log_option and save_log_option.lower() == "yes":
                save_log(symptoms, username)
                output["log"] = "📥 Log saved successfully."
        else:
            output["issue"] = "⚠️ Unknown symptoms. Please consult a doctor."
            output["advice"] = "Try entering common symptoms like fever, cough, etc."

    return render_template("index.html", output=output)

@app.route("/history")
def history():
    trends = get_user_trends("guest")  # Get trends for the user
    return render_template("history.html", trends=trends)

@app.route("/edit_symptom", methods=["POST"])
def edit_symptom():
    symptom = request.form.get("symptom")
    trends = get_user_trends("guest")  # Get trends again to pass to the template
    if symptom:
        matched = []
        for key_symptom in SYMPTOM_DB.keys():
            if re.search(r'\b' + re.escape(key_symptom) + r'\b', symptom.lower()):
                matched.append((key_symptom, SYMPTOM_DB[key_symptom]))

        return render_template("edit_symptom.html", matched=matched, trends=trends)

    return redirect(url_for('index'))

from flask import session, redirect, url_for, request

@app.route('/delete_symptom/<symptom>', methods=['POST'])
def delete_symptom(symptom):
    trends = session.get('trends', {})
    if symptom in trends:
        del trends[symptom]
        session['trends'] = trends  # save back the updated trends
    return redirect(url_for('history'))


@app.route("/clear_logs", methods=["POST"])
def clear_logs():
    with open("symptoms.txt", "w") as file:
        file.truncate(0)  # Clear log file
    return redirect(url_for("index"))

@app.route("/research")
def research():
    return render_template("research.html")


if __name__ == "__main__":
    app.run(debug=True)
