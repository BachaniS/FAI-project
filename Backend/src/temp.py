from pymongo import MongoClient
from typing import Dict

def update_course_descriptions():
    """
    Updates course descriptions in the MongoDB database.
    This is a one-time function to populate course descriptions.
    """
    # MongoDB Connection
    MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"
    client = MongoClient(MONGO_URI)
    db = client["subject_details"]
    courses_collection = db["courses"]
    
    # Dictionary mapping course IDs to their descriptions
    course_descriptions: Dict[str, str] = {
        "CS5004": "A comprehensive introduction to object-oriented programming principles and design. This course covers fundamental concepts including classes, inheritance, polymorphism, and design patterns. Students will gain hands-on experience with Java and other OOP languages while learning best practices in software design and development.",
        
        "CS5008": "An in-depth exploration of fundamental data structures and algorithms within computer systems. The course covers implementation and analysis of essential data structures, algorithmic techniques, and their applications in solving computational problems. Students will learn both theoretical concepts and practical implementation.",
        
        "CS5097": "An immersive course in mixed reality development, covering both virtual and augmented reality technologies. Students learn to create interactive 3D experiences using industry-standard tools like Unity and Unreal Engine, while exploring the principles of spatial computing and human-computer interaction in immersive environments.",
        
        "CS5100": "A foundational course in artificial intelligence covering core concepts and techniques. Topics include search algorithms, knowledge representation, logical reasoning, and machine learning. Students will implement AI solutions using Python while exploring both classical and modern approaches to artificial intelligence.",
        
        "CS5180": "Advanced course focusing on reinforcement learning and sequential decision making. Students learn theoretical foundations and practical applications of RL, including Markov Decision Processes, Q-learning, and policy optimization. Includes hands-on implementation of RL algorithms for real-world problems.",
        
        "CS5200": "Comprehensive study of database management systems, covering both theoretical and practical aspects. Topics include database design, SQL, transaction management, and data modeling. Students gain hands-on experience with modern database technologies while learning about data organization and retrieval.",
        
        "CS5310": "Introduction to computer graphics principles and techniques. Covers 2D and 3D graphics programming, rendering algorithms, and geometric modeling. Students learn both theoretical foundations and practical implementation using modern graphics APIs.",
        
        "CS5330": "Advanced course in computer vision and pattern recognition. Covers image processing, feature detection, object recognition, and machine learning applications in computer vision. Students implement vision algorithms and work with real-world image data.",
        
        "CS5335": "Comprehensive introduction to robotics principles and systems. Covers robot kinematics, control systems, sensor integration, and autonomous navigation. Students work with both simulated and physical robotic systems.",
        
        "CS5340": "Study of human-computer interaction principles and interface design. Covers user research, interface prototyping, usability testing, and interaction design patterns. Students create and evaluate user interfaces while considering human factors and accessibility.",
        
        "CS5350": "Advanced course in geometric computation and representation. Covers computational geometry algorithms, 3D modeling techniques, and geometric transformations. Students implement geometric algorithms and work with various representation schemes.",
        
        "CS5360": "Specialized course in non-interactive computer graphics focusing on ray tracing, global illumination, and shader programming. Students learn advanced rendering techniques and implement realistic graphics systems.",
        
        "CS5400": "In-depth study of programming language principles, including syntax, semantics, and language design. Covers various programming paradigms and their implementation. Students analyze and implement language features while understanding theoretical foundations.",
        
        "CS5500": "Comprehensive introduction to software engineering principles and practices. Covers the entire software development lifecycle, including requirements analysis, design, testing, and project management. Students work in teams using modern development methodologies.",
        
        "CS5520": "Practical course in mobile application development focusing on Android platform. Covers UI design, data storage, network communication, and mobile-specific considerations. Students build complete mobile applications using Java/Kotlin and Android Studio.",
        
        "CS5540": "Hands-on course in game programming using industry-standard engines. Covers game design principles, physics simulation, AI for games, and multiplayer networking. Students create playable games while learning about game engine architecture.",
        
        "CS5600": "Fundamental course in computer systems covering operating systems, memory management, and system programming. Students learn low-level programming in C while understanding how computer systems work at the hardware-software interface.",
        
        "CS5610": "Comprehensive course in modern web development. Covers front-end technologies (HTML, CSS, JavaScript), back-end development, databases, and web security. Students build full-stack web applications using current frameworks and best practices.",
        
        "CS5700": "In-depth study of computer networking fundamentals. Covers TCP/IP protocols, routing algorithms, network security, and distributed systems. Students implement networking protocols and understand modern network architectures.",
        
        "CS5800": "Advanced course in algorithm design and analysis. Covers algorithm complexity, dynamic programming, graph algorithms, and optimization techniques. Students implement and analyze efficient algorithms for solving complex computational problems.",
        
        "CS5965": "Professional development course focusing on industry collaboration. Students work with industry partners on real-world projects while developing professional skills and understanding industry practices.",
        
        "CS6200": "Advanced course in information retrieval systems. Covers search algorithms, text processing, ranking methods, and evaluation metrics. Students implement search systems while learning about modern IR techniques.",
        
        "DS5010": "Introduction to programming concepts specific to data science. Covers Python programming, data manipulation with Pandas, and basic data analysis techniques. Students learn to write efficient code for data science applications.",
        
        "DS5020": "Foundational mathematics course for data science. Covers linear algebra concepts and probability theory essential for machine learning and data analysis. Students learn both theoretical foundations and practical applications.",
        
        "DS5110": "Comprehensive course in data management and processing. Covers database systems, ETL pipelines, and big data technologies. Students learn to work with various data storage and processing systems.",
        
        "DS5220": "In-depth study of supervised machine learning algorithms and learning theory. Covers classification, regression, model evaluation, and theoretical foundations. Students implement and evaluate machine learning models.",
        
        "DS5230": "Advanced course in unsupervised learning and data mining techniques. Covers clustering, dimensionality reduction, and pattern discovery methods. Students work with real-world datasets to uncover hidden patterns.",
        
        "DS5500": "Capstone course in data science where students apply their knowledge to real-world problems. Includes data wrangling, analysis, and machine learning implementation. Students complete end-to-end data science projects.",
        
        "CS6120": "Advanced course in natural language processing. Covers text processing, language models, and modern transformer architectures. Students implement NLP systems using current technologies like BERT and GPT.",
        
        "CS6130": "Innovative course in affective computing and emotion recognition. Covers biosignal processing, emotion detection algorithms, and ethical considerations. Students work with emotional computing systems.",
        
        "CS6140": "Comprehensive machine learning course covering both theory and practice. Students learn various ML algorithms, feature engineering, and model evaluation while implementing solutions using modern frameworks.",
        
        "CS6220": "Advanced course in data mining techniques. Covers classification, prediction, and ensemble methods for large-scale data analysis. Students work with real-world datasets using modern data mining tools.",
        
        "CS6240": "Specialized course in parallel data processing. Covers distributed computing frameworks, MapReduce, and cloud platforms. Students implement parallel algorithms using technologies like Hadoop and Spark.",
        
        "CS6640": "Advanced course in operating systems implementation. Students learn kernel development, file systems, and multithreading while implementing OS components.",
        
        "CS6650": "Advanced course in distributed systems focusing on scalability. Covers distributed algorithms, consensus protocols, and system design. Students build scalable distributed applications.",
        
        "CS7150": "Advanced course in deep learning. Covers neural network architectures, training techniques, and practical applications. Students implement deep learning models using PyTorch and TensorFlow.",
        
        "CS7200": "Advanced course in statistical methods for computer science. Covers applied statistics, Bayesian inference, and statistical learning theory. Students apply statistical methods to computer science problems.",
        
        "CS7400": "Advanced study of programming language principles. Covers language design, implementation, and formal semantics. Students analyze and implement various programming language features.",
        
        "CS7600": "Intensive course in computer systems covering advanced topics in operating systems, distributed systems, and system architecture. Students implement complex system components.",
        
        "CS5001": "Introductory course to computer science and programming fundamentals. Students learn basic programming concepts, problem-solving strategies, and algorithmic thinking. The course provides hands-on experience with Python programming while building a strong foundation in computational thinking.",
        
        "CS5005": "Introduction to computational thinking and problem solving. This course focuses on developing analytical skills through algorithmic design, abstraction, and basic programming concepts. Students learn to break down complex problems and develop efficient solutions.",
        
        "CS5009": "Advanced programming concepts and data structures laboratory. This hands-on course reinforces theoretical concepts through practical implementation of data structures and algorithms. Students gain experience with debugging, testing, and code optimization.",
        
        "CS5010": "Comprehensive introduction to programming design paradigms. Covers functional programming, object-oriented design, and recursive problem solving. Students develop strong programming fundamentals while learning to write clean, maintainable code.",
        
        "CS5320": "Advanced computer vision and digital image processing. Covers image enhancement, segmentation, feature extraction, and 3D vision. Students work with real-world computer vision applications and modern deep learning frameworks.",
        
        "CS5520": "Mobile application development with focus on modern platforms. Students learn mobile UI design principles, data persistence, network programming, and platform-specific features while building complete mobile applications.",
        
        "CS5800": "Advanced algorithms and complexity analysis. Covers algorithm design techniques, complexity classes, optimization problems, and approximation algorithms. Students analyze and implement sophisticated algorithmic solutions.",
        
        "CS5850": "Advanced parallel algorithms and architectures. Students learn parallel computing paradigms, distributed algorithms, and performance optimization techniques. Includes hands-on experience with parallel programming frameworks.",
        
        "CS6140": "Advanced machine learning techniques and applications. Covers supervised and unsupervised learning, deep learning, and reinforcement learning. Students implement complex ML systems using modern frameworks.",
        
        "CS6160": "Advanced computer vision and scene understanding. Focuses on 3D vision, motion analysis, object tracking, and advanced deep learning applications in computer vision. Students work on cutting-edge vision problems.",
        
        "CS6300": "Theory of computation and formal languages. Covers automata theory, computability, complexity theory, and formal language hierarchies. Students explore theoretical foundations of computer science.",
        
        "CS6350": "Advanced computer graphics and visualization. Covers real-time rendering, global illumination, physics-based animation, and scientific visualization. Students implement sophisticated graphics applications.",
        
        "CS6410": "Compilers and program analysis. Covers lexical analysis, parsing, semantic analysis, and code generation. Students implement compiler components and learn program optimization techniques.",
        
        "CS6510": "Advanced software design and development. Focuses on large-scale software architecture, design patterns, and modern development practices. Students work on complex software projects using enterprise technologies.",
        
        "CS6710": "Network security and cryptography. Covers security protocols, cryptographic algorithms, network attacks and defenses. Students implement security solutions and analyze system vulnerabilities.",
        
        "CS6760": "Advanced distributed computing and systems. Covers distributed algorithms, fault tolerance, consistency models, and distributed data management. Students build robust distributed applications.",
        
        "CS6800": "Advanced algorithms and complexity theory. Explores randomized algorithms, approximation algorithms, and computational complexity. Students analyze and implement sophisticated algorithmic solutions.",
        
        "CS7180": "Special topics in artificial intelligence. Covers current research areas in AI, including deep learning, natural language processing, and reinforcement learning. Students work on cutting-edge AI projects.",
        
        "CS7280": "Special topics in software development. Explores emerging technologies, methodologies, and best practices in software engineering. Students work on innovative software projects.",
        
        "CS7380": "Special topics in computer systems. Covers advanced topics in operating systems, distributed systems, and cloud computing. Students implement complex system components.",
        
        "INFO5100": "Application engineering and development. Focuses on software development lifecycle, requirements engineering, and project management. Students build enterprise applications using modern frameworks.",
        
        "INFO6105": "Data science engineering methods and tools. Covers the complete data science pipeline, from data collection to deployment. Students work with big data technologies and machine learning frameworks.",
        
        "INFO6150": "Web design and user experience engineering. Focuses on modern web development, responsive design, and user experience principles. Students create sophisticated web applications.",
        
        "INFO6205": "Program structures and algorithms. Covers advanced data structures, algorithm design, and optimization techniques. Students implement efficient solutions to complex computational problems.",
        
        "INFO6250": "Web development tools and methods. Explores modern web frameworks, development tools, and deployment strategies. Students build full-stack web applications using current technologies."
    }
    
    # Update descriptions in the database
    updated_count = 0
    for subject_id, description in course_descriptions.items():
        result = courses_collection.update_one(
            {"subject_id": subject_id},
            {"$set": {"description": description}}
        )
        if result.modified_count > 0:
            updated_count += 1
            
    print(f"Updated descriptions for {updated_count} courses")
    
    # Close the connection
    client.close()

# You can run this function to update all course descriptions
if __name__ == "__main__":
    update_course_descriptions()