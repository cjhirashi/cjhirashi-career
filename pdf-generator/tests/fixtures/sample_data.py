"""Sample data for testing."""


def get_sample_cv_data():
    """Get sample CV data for testing."""
    return {
        "name": "Carlos Jiménez Hirashi",
        "email": "cjhirashi@gmail.com",
        "phone": "+34 666 777 888",
        "location": "Madrid, Spain",
        "ikigai": "Empower teams through scalable architecture and mentorship, combining technical excellence with human-centered leadership",
        "about": "Senior Backend Engineer with 10+ years of experience in building scalable distributed systems. Passionate about clean code, mentoring junior developers, and driving architectural innovation. Proven track record leading teams through complex technical challenges and delivering high-impact projects.",
        "competencies": [
            {
                "category": "Programming Languages",
                "name": "Python",
                "level": "Expert",
            },
            {
                "category": "Programming Languages",
                "name": "Go",
                "level": "Advanced",
            },
            {
                "category": "Frameworks & Tools",
                "name": "FastAPI",
                "level": "Expert",
            },
            {
                "category": "Frameworks & Tools",
                "name": "PostgreSQL",
                "level": "Expert",
            },
            {
                "category": "Architecture",
                "name": "Microservices",
                "level": "Expert",
            },
            {
                "category": "Architecture",
                "name": "System Design",
                "level": "Advanced",
            },
            {
                "category": "Leadership",
                "name": "Team Management",
                "level": "Advanced",
            },
            {
                "category": "Leadership",
                "name": "Mentoring",
                "level": "Advanced",
            },
        ],
        "experience": [
            {
                "position": "Senior Backend Engineer",
                "company": "Tech Company X",
                "start_date": "2022-01",
                "end_date": "present",
                "description": "Led architecture redesign of monolithic application, resulting in 40% performance improvement. Mentored team of 5 junior engineers. Implemented microservices-based architecture using FastAPI and PostgreSQL.",
            },
            {
                "position": "Backend Engineer",
                "company": "Startup Y",
                "start_date": "2019-06",
                "end_date": "2021-12",
                "description": "Built and maintained core APIs serving 500K+ daily active users. Implemented caching strategies reducing database load by 60%. Led on-call rotation and incident response.",
            },
            {
                "position": "Junior Developer",
                "company": "Company Z",
                "start_date": "2017-03",
                "end_date": "2019-05",
                "description": "Developed Python and JavaScript applications. Participated in code reviews and learned best practices from senior engineers.",
            },
        ],
        "education": [
            {
                "degree": "Master's Degree",
                "school": "Universidad Autónoma de Madrid",
                "field": "Computer Science",
                "year": "2017",
            },
            {
                "degree": "Bachelor's Degree",
                "school": "Universidad Politécnica de Madrid",
                "field": "Electrical Engineering",
                "year": "2015",
            },
        ],
        "projects": [
            {
                "name": "Distributed Task Queue",
                "description": "Built high-performance task queue system handling 1M+ messages/day with Redis and FastAPI",
                "technologies": ["Python", "FastAPI", "Redis", "PostgreSQL"],
                "link": "https://github.com/example/task-queue",
            },
            {
                "name": "Real-time Analytics Platform",
                "description": "Developed real-time analytics dashboard using streaming data and WebSockets",
                "technologies": ["Python", "FastAPI", "WebSockets", "React"],
                "link": "https://github.com/example/analytics",
            },
        ],
    }


def get_sample_cover_letter_data():
    """Get sample Cover Letter data for testing."""
    return {
        "name": "Carlos Jiménez Hirashi",
        "email": "cjhirashi@gmail.com",
        "date": "2024-08-16",
        "company_name": "Tech Company Inc.",
        "company_address": "123 Tech Street, San Francisco, CA 94105, USA",
        "recipient_name": "Jane Smith",
        "position": "Senior Backend Engineer",
        "body": """Your organization's commitment to building scalable infrastructure and fostering innovation aligns perfectly with my professional values and experience. With over 10 years of backend development expertise and a track record of leading successful microservices implementations, I am confident I can significantly contribute to your team's mission.

In my current role at Tech Company X, I have successfully architected and deployed microservices that increased system performance by 40% while reducing operational costs. My experience spans Python, Go, PostgreSQL, and modern cloud technologies, and I have a proven ability to mentor and develop engineering teams.

I am particularly drawn to your company's focus on technology excellence and engineering culture. I believe my background in system design, performance optimization, and team leadership would make me a valuable addition to your organization.""",
        "closing_statement": "I look forward to discussing how I can contribute to your team's success and help drive technical innovation at your organization.",
        "signature": "Carlos Jiménez Hirashi",
    }


def get_minimal_cv_data():
    """Get minimal CV data for testing (required fields only)."""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1 555 1234",
        "location": "New York, USA",
        "ikigai": "Build great software that helps people",
        "about": "Software engineer with several years of experience building web applications",
        "competencies": [
            {"category": "Programming", "name": "Python", "level": "Intermediate"},
        ],
        "experience": [],
        "education": [],
        "projects": [],
    }


def get_minimal_cover_letter_data():
    """Get minimal Cover Letter data for testing (required fields only)."""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "date": "2024-08-16",
        "company_name": "Example Corp",
        "company_address": "456 Main St, Boston, MA",
        "recipient_name": "Mr. Hiring Manager",
        "position": "Software Engineer",
        "body": "I am writing to express my strong interest in the Software Engineer position at your esteemed organization. With my solid foundation in software development and passion for building quality applications, I am confident in my ability to contribute meaningfully to your team.",
        "closing_statement": "Thank you for considering my application.",
        "signature": "John Doe",
    }
