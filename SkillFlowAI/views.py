import os
import json
import re
import datetime
import random
import string

from django.conf import settings
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect, redirect
from django.views.decorators.csrf import csrf_exempt

import requests 
import fitz  # PyMuPDF for extracting text from PDFs

import http.client

from openai import OpenAI

from .models import *

### MUST EXPORT OPEN AI API KEY ON COMMANDLINE ###
# export OPEN_AI_KEY=sk-....

client = OpenAI()

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        # Check if the user has uploaded a resume
        resume_uploaded = bool(request.user.resume and request.user.resume.strip())  # Checks if resume exists and isn't empty

        return render(request, "SkillFlowAI/index.html", {
            "email": request.user.email,
            "resumeUploaded": resume_uploaded
        })
    else:
        return render(request, "SkillFlowAI/index.html", {
            "email": "",
            "resumeUploaded": False  # Default to False if user isn't authenticated
        })
    
def register(request):
    if request.method == "POST":
        email = request.POST["username"]
        email = email.lower()
        if email == "":
                return render(request, "SkillFlowAI/register.html", {
                    "error": "please enter an email",
                })
        elif "@" not in email:
            return render(request, "SkillFlowAI/register.html", {
                "email": email,
                "error": "please enter a valid email",
            })
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password == confirmation:      
            try:
                user = User.objects.create_user(username=email, email=email, password=password)
                user.save()
            except IntegrityError:
                return render(request, "SkillFlowAI/register.html", {
                    "email": email,
                    "error": "That email was already taken."
                })
            login(request, user)
            return HttpResponseRedirect("/")
        else:
            return render(request, "SkillFlowAI/register.html", {
                "email": email,
                "error": "Your pasword does not match your confirmation password",
            })
    else:
        return render(request, "SkillFlowAI/register.html", {
        })

def logoutView(request):
    logout(request)
    return HttpResponseRedirect("/login")

def loginView(request):
    if request.method == "POST":
        email = request.POST["username"]
        password = request.POST["password"]
        email = email.lower()
        user = authenticate(request, username=email, password=password)
        print(user)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect("/")
        else:
            return render(request, "SkillFlowAI/login.html", {
                "error": "Incorrect email or password",
                "email": email,
            })
    else:
        if request.user.is_authenticated != True:
            return render(request, "SkillFlowAI/login.html", {
                "email": "",
            })
        else:
            return HttpResponseRedirect("/")

# LinkedIn Job Search API credentials
RAPIDAPI_KEY = "insert API Key Here"
RAPIDAPI_HOST = "linkedin-job-search-api.p.rapidapi.com"
JOBS_API_URL = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-24h"

@csrf_exempt
@login_required(login_url="login")
def chatAPI(request):
    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()

        if not prompt:
            return JsonResponse({"error": "Prompt cannot be empty"}, status=400)

        try:
            # Retrieve past chat history for context (last 10 messages)
            past_messages = list(ChatHistory.objects.filter(user=request.user)
                                .order_by("timestamp")
                                .values_list("user_input", "chat_output"))

            chat_context = []
            for user_input, ai_response in past_messages[-10:]:  
                chat_context.append({"role": "user", "content": user_input})
                chat_context.append({"role": "assistant", "content": ai_response})

            chat_context.append({"role": "user", "content": prompt})

            # System instruction to enforce JSON structure
            chat_context.append({
                "role": "system",
                "content": (
                    "You are JobBot, an AI that provides job recommendations and resume feedback but only respond in JSON that is outlined below"
                    "The user has uploaded their resume. Use this resume to extract **relevant job titles, skills, and location**."
                    "Additionally, the user may provide specific job search preferences (e.g., remote jobs, job type, location)."
                    "\n\n"
                    "### **Your Response Format** ###"
                    "Return your response **only** as a structured JSON object in this format:\n"
                    "```json\n"
                    "{\n"
                    "  \"natural_response\": \"A helpful response explaining the job search details\",\n"
                    "  \"job_search_query\": {\n"
                    "    \"title_filter\": \"Extracted Job Title\",\n"
                    "    \"location_filter\": \"Extracted or user-provided location\",\n"
                    "    \"description_filter\": \"Filter on the job description. You can search like you search on Google, but limit number of words to one\",\n"
                    "    \"date_posted\": \"all\",\n"
                    "    \"type_filter\": \"CONTRACTOR, FULL_TIME, INTERN, OTHER, PART_TIME, TEMPORARY, VOLUNTEER\",\n"
                    "    \"remote\": \"\", # true for remote jobs, false for on-site jobs, empty to include all\n"
                    "    \"page\": 1,\n"
                    "    \"num_pages\": 1\n"
                    "  }\n"
                    "}\n"
                    "```"
                    "\n\n"
                    "\n\n"
                    "### **IMPORTANT RULES** ###"
                    "- Extract job-related information **ONLY** from the resume and user input."
                    "- If **location is not specified**, return a general search without it. Prioritize interpretting people saying that want a job \"at somewhere\" as them mentioning that they want a job at a company over a specific location. Only pick the location if you are sure that is the location they are looking for. Omit otherwise."
                    "- If the user **does not specify job type**, use the default employment types. YOU MUST replace the employment_types from what is there to one of the four options mentioned in the example! All CAPS!"
                    "- Your response must be a **valid JSON object** with proper formatting and no missing fields."
                    "-title_filter: Filter on the job title. You can search like you search on Google, see the documentation for more info. Must be some sort of job position. Use user prompt first then resume to decide this. This shouldn't be more than a few words that are descriptive and on point"
                    "-location_filter: Filter on location. Please do not search on abbreviations like US, UK, NYC. Instead, search on full names like United States, New York, United Kingdom. You may filter on more than one location in a single API call using the OR parameter. For example: Dubai OR Netherlands OR Belgium"
                    "-desicription_filter: Filter on the job description. You can search like you search on Google, but limit number of words to one"
                    "-type_filter: Filter on a specific job type, the options are: CONTRACTOR, FULL_TIME, INTERN, OTHER, PART_TIME, TEMPORARY, VOLUNTEER;To filter on more than one job type, please delimitd by comma, like such: FULL_TIME, PART_TIME. If you are not sure which one the user prefers omit from the JSON"
                    "-remote: Set to 'true' to include remote jobs only. Set to 'false' to include jobs that are not remote. Leave empty to include both remote and non remote jobs. Omit if you do not know what the user prefers"
                    "-natural_response: give a response in the JSON item where there is a 'friendly' place holder explaining what jobs would be great for them and what they could explore"
                    "YOU MUST FILL IN THE JOB_REQUIREMENTS with one of the items in the listin the format example JSON. If you do not know just omit the line."
                    "\n\n"
                    "Now, generate the JSON job search query based on the resume and user request. ONLY PROVIDE JSON NOT PROMPT RESPONSE"
                )
            })

            # Send request to OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=chat_context,
                temperature=0.7
            )

            # Extract AI response content
            full_ai_response = response.choices[0].message.content.strip()

            # Parse AI response into JSON
            try:
                match = re.search(r"\{[\s\S]*\}", full_ai_response)  # Finds JSON inside response
                response_json = json.loads(match.group(0))  # Convert extracted string to JSON
                natural_response = response_json.get("natural_response", "")
                job_search_query = response_json.get("job_search_query", {})

                # If job_search_query is empty, return an error
                if not job_search_query:
                    return JsonResponse({"error": "Job search query is missing in AI response", "ai_response": full_ai_response}, status=400)

            except json.JSONDecodeError:
                return JsonResponse({"error": "AI response was not valid JSON", "raw_response": full_ai_response}, status=500)
            # **Submit job search query to LinkedIn Job Search API**
            
            print(full_ai_response)
            query_params = {key: str(value) for key, value in job_search_query.items() if value}  # Convert to string for URL params
            
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": RAPIDAPI_HOST
            }

            job_search_response = requests.get(JOBS_API_URL, headers=headers, params=query_params)

            # Handle LinkedIn API response
            if job_search_response.status_code == 200:
                job_listings = job_search_response.json()
            else:
                job_listings = {"error": f"Failed to fetch job listings: {job_search_response.text}"}

            # Save conversation in database
            ChatHistory.objects.create(
                user=request.user,
                user_input=prompt,
                chat_output=natural_response,
                jobListing=job_listings
            )

            # **Delete old chat history beyond 20 entries**
            user_chats = ChatHistory.objects.filter(user=request.user).order_by("timestamp")
            if user_chats.count() > 20:
                user_chats.first().delete()

        except Exception as e:
            print(full_ai_response)
            print(f"Error contacting OpenAI: {str(e)}")
            return JsonResponse({"error": f"Error contacting OpenAI: {str(e)}"}, status=500)

        return JsonResponse({
            "user_input": prompt,
            "ai_response": natural_response,  
            "job_search_params": job_search_query,  
            "job_listings": job_listings  # Retrieved jobs from LinkedIn API
        })
    else:
        # Retrieve chat history for the logged-in user
        chat_history = ChatHistory.objects.filter(user=request.user).order_by("timestamp")

        chat_list = [
            {
                "timestamp": chat.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "user_input": chat.user_input,
                "chat_output": chat.chat_output,
                "jobListing": chat.jobListing  
            }
            for chat in chat_history
        ]

        return JsonResponse({"chat_history": chat_list})
    
@csrf_exempt
@login_required(login_url="login")
def chatAPIUpload(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("file")

        if not uploaded_file or not uploaded_file.name.endswith(".pdf"):
            return JsonResponse({"error": "Please upload a valid PDF file."}, status=400)

        try:
            pdf_text = ""

            # Read and extract text from the PDF file
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as pdf_document:
                for page in pdf_document:
                    pdf_text += page.get_text("text") + "\n"

            # Save extracted text into the user's resume field
            request.user.resume = pdf_text
            request.user.save()
            request.user.refresh_from_db()  # Ensure the latest data is loaded

            print(f"Resume successfully saved! First 200 chars: {pdf_text[:200]}...")  # Debugging log

            return JsonResponse({"success": "Resume uploaded and processed successfully.", "resume_text": pdf_text[:500] + "... (truncated)"})

        except Exception as e:
            print(f"PDF Processing Error: {str(e)}")
            return JsonResponse({"error": f"Failed to process PDF: {str(e)}"}, status=500)

    elif request.method == "GET":
        try:
            # Count chat history records before deleting
            chat_count = ChatHistory.objects.filter(user=request.user).count()

            if chat_count == 0:
                return JsonResponse({"success": "No chat history to clear."})

            # Delete all chat history records for the logged-in user
            deleted_count, _ = ChatHistory.objects.filter(user=request.user).delete()

            return JsonResponse({"success": f"Cleared {deleted_count} chat history records for user."})

        except Exception as e:
            print(f"⚠ Error clearing chat history: {str(e)}")
            return JsonResponse({"error": f"Failed to clear chat history: {str(e)}"}, status=500)
        
    return JsonResponse({"error": "Invalid request method."}, status=405)