# SkillFlowAI
SkillsFlowAI is an AI-driven job-matching platform that analyzes your resume and chat messages to recommend tailored job opportunities. JobBot's assistance will help you find your ideal role!

## Inspiration
Searching for summer jobs is extremely frustrating for me. No matter where I looked, I struggled to find positions that matched my resume and interests. The filters on job sites were time-consuming to index through and were often very inefficient. I wasted time scrolling through posts that were irrelevant to me. I realized that in today's job market, getting accepted to a job that matches your skills, passions, and preferences is very hard.

I built SkillsFlowAI to solve this problem. Instead of navigating through endless listings, this AI-powered platform will deliver instant, precise job recommendations that will truly align with what you're looking for. Focus on what's available and avoid wasting time by preventing searches for what never existed!

## What SkillFlowAI does

SkillFlowAI is an AI-powered job-matching platform that's designed to simplify your job search. Once the user creates an account, they can upload and save their resume to allow the AI-driven **JobBot** to provide **instant** job recommendations on the user's resume and chat with the bot. The system ensures a seamless experience by saving user chat history and the latest job recommendations so that users can always pick up where they left off. With every interaction, the AI will generate a natural response, tailoring responses for your skills & preferences, as well as delivering **relevant job opportuntities** based on _your_ criteria without the hassles of endless searching and filtering.

## How we built it
### The Project consists of:
- Web Application: Built using Django, Javascript, and Bootstrap
- Job Search Integration: Uses AI queries to take job listings from LinkedIn's jobs catalog through RapidAPI
- OpenAI integration: Uses OpenAI API to process user input, but the application separately manages chat history and user data so that the AI always has relevant context & resume
- Resume Extraction: Uses Python libraries to extract information from resume PDFs and stores them in a database, associating them with the user

## Challenges we ran into
- Data accuracy: Ensuring that AI queries and recommendations were tailored and relevant
- Job Listing Availability: Creating better querying methods so that queries weren't so specific such that the results were none but specific enough such that job results were accurate and preferable.
- User Experience: Making chatbot feel intuitive and creating an experience that quickly responds with job opportunities.

## Accomplishments that we're proud of
- Instant job recommendations based on user input and resume
- Optimized search process that uses OpenAI's API to streamline results to be accurate and eliminates the irrelevant results.
- Designing a smooth and clean UI that creates an effortless job search and increases the interaction of the user with the application

## What we learned
- User job-finding frustration is real - many people struggle with inefficient job searching platforms
- AI prompting and proper data feeding to ensure that AI returns responses that are accurate and formatted such that traditional programs can use its responses
- Determining the best AI models to perform various tasks (ex: creating parsed JSON vs very creative writing)

## What's next for SkillFlowAI
- **Expanding job sources:** Provide a larger array of listings than that of the current API used
- **System of saving opportunities:** Save/bookmark job opportunities and use this information to increase the catering of AI responses with relevant job opportunities
- **Using data:** using data collected from users to improve and cater an AI model just for finding jobs

## Procedure to run project
You must have an API key that has access to the OPENAI API. You can export this key in the working directory with export OPEN_AI_KEY=sk-...

You must also have a rapid API key for linked in job database. You will have to insert that API key into views.py where it says RAPIDAPI_KEY = "insert API Key Here"

You can go to the working directory of the django project and run "python(3) manage.py runserver" if you want to see how the project works.