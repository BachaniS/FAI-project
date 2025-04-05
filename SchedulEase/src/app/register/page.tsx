'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { interestCategories } from './interestCategories';

const PROGRAMMING_LANGUAGES = [
  'Assembly', 'C', 'C#', 'C++', 'Go', 'Haskell', 'Java', 'JavaScript',
  'Kotlin', 'MATLAB', 'Python', 'R', 'Rust', 'SQL', 'Scala'
];

const MATH_TOPICS = [
  'Algorithms', 'Applied statistics', 'Basic Statistics', 'Basic knowledge of Statistics',
  'Bayesian inference', 'CAP Theorem', 'Calculus', 'Combinatorics',
  'Complexity Analysis', 'Decision', 'Decision Trees', 'Differential Calculus',
  'Discrete Mathematics', 'Geometric transformations', 'Graph Theory', 'Lexical Analysis',
  'Linear Algebra', 'Logic', 'Markov', 'Matrix operations',
  'Probability', 'Regression', 'Rendering Optimization', 'Sentiment Analysis',
  'Set Theory', 'Statistics', 'Transformers', 'vector space models'
];

interface Experience {
  [key: string]: number;
}

interface Course {
  code: string;
  name: string;
  weeklyWorkload: number;
  finalGrade: number;
  experience: number;
}

interface CoreRequirement {
  subjectCode: string;
}

interface Interest {
  category: string;
  topics: string[];
}

interface StudentData {
  NUID: string;
  name: string;
  programming_experience: { [key: string]: number };
  math_experience: { [key: string]: number };
  completed_courses: Array<{
    subject_code: string;
    course_name: string;
    weekly_workload: number;
    final_grade: string;
    experience_rating: number;
  }>;
  core_subjects: string[];
  desired_outcomes: { [key: string]: string[] };
}

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [nuid, setNuid] = useState('');
  const [fullName, setFullName] = useState('');
  const [programmingExperience, setProgrammingExperience] = useState<Experience>({});
  const [mathExperience, setMathExperience] = useState<Experience>({});
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [completedCourses, setCompletedCourses] = useState<Course[]>([]);
  const [currentCourse, setCurrentCourse] = useState<Course>({
    code: '',
    name: '',
    weeklyWorkload: 0,
    finalGrade: 0,
    experience: 0
  });
  const [isAddingCourse, setIsAddingCourse] = useState(false);
  const [coreRequirements, setCoreRequirements] = useState<CoreRequirement[]>([]);
  const [currentSubject, setCurrentSubject] = useState('');
  const [selectedInterests, setSelectedInterests] = useState<Interest[]>([]);
  const [currentCategory, setCurrentCategory] = useState<string>('');
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    if (step === 2) {
      setStep(3);
    } else if (step === 3) {
      setStep(4);
    } else if (step === 4) {
      setStep(5);
    } else if (step === 5) {
      setStep(6);
    }
  };

  const handleBack = () => {
    setStep(step - 1);
  };

  const handleProficiencyChange = (language: string, proficiency: number) => {
    setProgrammingExperience(prev => ({
      ...prev,
      [language]: proficiency
    }));
  };

  const handleMathProficiencyChange = (topic: string, proficiency: number) => {
    setMathExperience(prev => ({
      ...prev,
      [topic]: proficiency
    }));
  };

  const handleAddCourse = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentCourse.code && currentCourse.name) {
      setCompletedCourses(prev => [...prev, currentCourse]);
      setCurrentCourse({
        code: '',
        name: '',
        weeklyWorkload: 0,
        finalGrade: 0,
        experience: 0
      });
      setIsAddingCourse(false);
    }
  };

  const handleDeleteCourse = (courseIndex: number) => {
    setCompletedCourses(prev => prev.filter((_, index) => index !== courseIndex));
  };

  const handleAddCoreRequirement = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentSubject.trim()) {
      setCoreRequirements(prev => [...prev, { subjectCode: currentSubject.trim() }]);
      setCurrentSubject('');
    }
  };

  const handleDeleteCoreRequirement = (index: number) => {
    setCoreRequirements(prev => prev.filter((_, i) => i !== index));
  };

  const handleAddInterest = () => {
    if (currentCategory && selectedTopics.length > 0) {
      setSelectedInterests(prev => [...prev, {
        category: currentCategory,
        topics: selectedTopics
      }]);
      setCurrentCategory('');
      setSelectedTopics([]);
    }
  };

  const handleDeleteInterest = (index: number) => {
    setSelectedInterests(prev => prev.filter((_, i) => i !== index));
  };

  const handleTopicToggle = (topic: string) => {
    setSelectedTopics(prev => 
      prev.includes(topic)
        ? prev.filter(t => t !== topic)
        : [...prev, topic]
    );
  };

  const handleFirstStepSubmit = async () => {
    if (!nuid || !fullName) {
      setError('Please enter both NUID and name');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nuid: nuid,
          name: fullName
        })
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.message || 'Registration failed, the user already exists');
        return;
      }

      // If we get here, user doesn't exist and we can proceed
      setStep(2);
    } catch (error) {
      console.error('Error checking user:', error);
      setError('An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (selectedInterests.length === 0) {
      alert('Please select at least one interest area before proceeding.');
      return;
    }

    setIsLoading(true);
    try {
      console.log('Current state values:', {
        selectedInterests,
        programmingExperience,
        mathExperience,
        completedCourses,
        coreRequirements
      });

      // Format interests as a simple array of strings
      const interests = selectedInterests.flatMap(interest => interest.topics);
      console.log('Formatted interests:', interests);

      // Prepare the student data
      const studentData = {
        nuid: nuid,
        name: fullName,
        interests: interests,
        programming_experience: programmingExperience,
        math_experience: mathExperience,
        completed_courses: completedCourses,
        core_subjects: coreRequirements.map(req => req.subjectCode)
      };

      // Log the final data being sent
      console.log('Data being sent to backend:', studentData);
      console.log('Stringified data:', JSON.stringify(studentData));

      const response = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(studentData),
      });

      // Log the response
      console.log('Response status:', response.status);
      const responseData = await response.json();
      console.log('Response data:', responseData);

      if (!response.ok) {
        throw new Error(responseData.message || 'Registration failed');
      }

      localStorage.setItem('user_data', JSON.stringify(studentData));
      router.push('/dashboard');
    } catch (error) {
      console.error('Registration error:', error);
      alert(error instanceof Error ? error.message : 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (step) {
      case 1:
        return (
          <div className="max-w-md w-full space-y-8">
            <div>
              <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Create your account
              </h2>
              <p className="mt-2 text-center text-sm text-gray-600">
                Step 1: Basic Information
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                <span className="block sm:inline">{error}</span>
              </div>
            )}

            {error && error.includes('Please login') && (
              <div className="text-center mt-4">
                <a
                  href="/login"
                  className="font-medium text-blue-600 hover:text-blue-500"
                >
                  Go to Login Page
                </a>
              </div>
            )}

            <form className="mt-8 space-y-6" onSubmit={(e) => {
              e.preventDefault();
              handleFirstStepSubmit();
            }}>
              <div className="rounded-md shadow-sm -space-y-px">
                <div>
                  <label htmlFor="nuid" className="sr-only">NUID</label>
                  <input
                    id="nuid"
                    name="nuid"
                    type="text"
                    required
                    value={nuid}
                    onChange={(e) => setNuid(e.target.value)}
                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    placeholder="NUID"
                  />
                </div>
                <div>
                  <label htmlFor="name" className="sr-only">Full Name</label>
                  <input
                    id="name"
                    name="name"
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    placeholder="Full Name"
                  />
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white ${
                    isLoading ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
                  } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
                >
                  {isLoading ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Checking...
                  </span>
                  ) : (
                    'Next'
                  )}
                </button>
              </div>
            </form>
          </div>
        );

      case 2:
        return (
          <div className="max-w-6xl w-full space-y-8">
            <div>
              <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Programming Experience
              </h2>
              <p className="mt-2 text-center text-sm text-gray-600">
                Step 2: Rate your programming proficiency (1-5)
              </p>
            </div>
            <form className="mt-8 space-y-6" onSubmit={handleNext}>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {PROGRAMMING_LANGUAGES.map((language, index) => (
                  <div key={language} className="bg-white p-6 rounded-lg shadow-md">
                    <div className="flex flex-col space-y-4">
                      <span className="text-base font-medium text-gray-700 min-h-[2rem]">
                        {index + 1}. {language}
                      </span>
                      <div className="flex justify-center space-x-3">
                        {[1, 2, 3, 4, 5].map((rating) => (
                          <button
                            key={rating}
                            type="button"
                            onClick={() => handleProficiencyChange(language, rating)}
                            className={`w-10 h-10 rounded-full text-base ${
                              programmingExperience[language] === rating
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                            }`}
                          >
                            {rating}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex space-x-4">
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Next
                </button>
              </div>
            </form>
          </div>
        );

      case 3:
        return (
          <div className="max-w-7xl w-full space-y-8">
            <div>
              <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Mathematics Experience
              </h2>
              <p className="mt-2 text-center text-sm text-gray-600">
                Step 3: Rate your mathematics proficiency (1-5)
              </p>
            </div>
            <form className="mt-8 space-y-6" onSubmit={handleNext}>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {MATH_TOPICS.map((topic, index) => (
                  <div key={topic} className="bg-white p-6 rounded-lg shadow-md">
                    <div className="flex flex-col space-y-4">
                      <span className="text-base font-medium text-gray-700 min-h-[2.5rem] flex items-center">
                        {index + 1}. {topic}
                      </span>
                      <div className="flex justify-center space-x-3">
                        {[1, 2, 3, 4, 5].map((rating) => (
                          <button
                            key={rating}
                            type="button"
                            onClick={() => handleMathProficiencyChange(topic, rating)}
                            className={`w-10 h-10 rounded-full text-base ${
                              mathExperience[topic] === rating
                                ? 'bg-green-500 text-white'
                                : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                            }`}
                          >
                            {rating}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex space-x-4">
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Next
                </button>
              </div>
            </form>
          </div>
        );

      case 4:
        return (
          <div className="max-w-4xl w-full space-y-8">
            <div>
              <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Completed Courses
              </h2>
              <p className="mt-2 text-center text-sm text-gray-600">
                Step 4: Add your completed courses (optional)
              </p>
            </div>

            {completedCourses.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6 space-y-4">
                <h3 className="text-lg font-medium">Added Courses:</h3>
                <div className="space-y-4">
                  {completedCourses.map((course, index) => (
                    <div key={index} className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div className="space-y-2 flex-1">
                          <h4 className="font-medium">{course.code}: {course.name}</h4>
                          <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
                            <p>Weekly Hours: {course.weeklyWorkload}</p>
                            <p>Grade: {course.finalGrade}</p>
                            <p>Experience: {course.experience}/5</p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleDeleteCourse(index)}
                          className="ml-4 p-2 text-red-600 hover:text-red-800 hover:bg-red-100 rounded-full transition-colors"
                          title="Delete course"
                        >
                          <svg 
                            xmlns="http://www.w3.org/2000/svg" 
                            className="h-5 w-5" 
                            viewBox="0 0 20 20" 
                            fill="currentColor"
                          >
                            <path 
                              fillRule="evenodd" 
                              d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" 
                              clipRule="evenodd" 
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {isAddingCourse ? (
              <form onSubmit={handleAddCourse} className="bg-white shadow rounded-lg p-6 space-y-4">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Course Code
                    </label>
                    <input
                      type="text"
                      required
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                      value={currentCourse.code}
                      onChange={(e) => setCurrentCourse(prev => ({
                        ...prev,
                        code: e.target.value
                      }))}
                      placeholder="e.g., CS12345"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Course Name
                    </label>
                    <input
                      type="text"
                      required
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                      value={currentCourse.name}
                      onChange={(e) => setCurrentCourse(prev => ({
                        ...prev,
                        name: e.target.value
                      }))}
                      placeholder="Course name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Weekly Workload (hours)
                    </label>
                    <input
                      type="number"
                      required
                      min="0"
                      max="168"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                      value={currentCourse.weeklyWorkload || ''}
                      onChange={(e) => setCurrentCourse(prev => ({
                        ...prev,
                        weeklyWorkload: parseInt(e.target.value) || 0
                      }))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Final Grade (0-100)
                    </label>
                    <input
                      type="number"
                      required
                      min="0"
                      max="100"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                      value={currentCourse.finalGrade || ''}
                      onChange={(e) => setCurrentCourse(prev => ({
                        ...prev,
                        finalGrade: parseInt(e.target.value) || 0
                      }))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Experience Rating (1-5)
                    </label>
                    <div className="flex space-x-2 mt-2">
                      {[1, 2, 3, 4, 5].map((rating) => (
                        <button
                          key={rating}
                          type="button"
                          onClick={() => setCurrentCourse(prev => ({
                            ...prev,
                            experience: rating
                          }))}
                          className={`w-10 h-10 rounded-full ${
                            currentCourse.experience === rating
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                          }`}
                        >
                          {rating}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex space-x-4 mt-4">
                  <button
                    type="button"
                    onClick={() => setIsAddingCourse(false)}
                    className="flex-1 py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Add Course
                  </button>
                </div>
              </form>
            ) : (
              <div className="flex space-x-4">
                <button
                  type="button"
                  onClick={() => setIsAddingCourse(true)}
                  className="flex-1 py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Add a Course
                </button>
              </div>
            )}

            <div className="flex space-x-4">
              <button
                type="button"
                onClick={handleBack}
                className="flex-1 py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleNext}
                className="flex-1 py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                Next
              </button>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="max-w-4xl w-full space-y-8">
            <div>
              <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Core Requirements
              </h2>
              <p className="mt-2 text-center text-sm text-gray-600">
                Step 5: Enter required subjects for your program
              </p>
            </div>

            {coreRequirements.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-medium mb-4">Added Requirements:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {coreRequirements.map((req, index) => (
                    <div 
                      key={index}
                      className="flex items-center justify-between bg-gray-50 p-3 rounded-lg"
                    >
                      <span className="font-medium text-gray-700">
                        {req.subjectCode}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleDeleteCoreRequirement(index)}
                        className="text-red-600 hover:text-red-800 p-1 hover:bg-red-100 rounded-full transition-colors"
                        title="Remove requirement"
                      >
                        <svg 
                          xmlns="http://www.w3.org/2000/svg" 
                          className="h-5 w-5" 
                          viewBox="0 0 20 20" 
                          fill="currentColor"
                        >
                          <path 
                            fillRule="evenodd" 
                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" 
                            clipRule="evenodd" 
                          />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <form onSubmit={handleAddCoreRequirement} className="bg-white shadow rounded-lg p-6">
              <div className="flex space-x-4">
                <input
                  type="text"
                  value={currentSubject}
                  onChange={(e) => setCurrentSubject(e.target.value)}
                  placeholder="Enter subject code (e.g., CS5100)"
                  className="flex-1 border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                  pattern="[A-Za-z]{2,}\d{4}"
                  title="Please enter a valid subject code (e.g., CS5100)"
                />
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Add
                </button>
              </div>
              <p className="mt-2 text-sm text-gray-500">
                Format: Letters followed by 4 digits (e.g., CS5100, INFO6150)
              </p>
            </form>

            <div className="flex space-x-4">
              <button
                type="button"
                onClick={handleBack}
                className="flex-1 py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleNext}
                className="flex-1 py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                Next
              </button>
            </div>
          </div>
        );

      case 6:
        return (
          <div className="max-w-6xl w-full mx-auto space-y-8 p-6">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900">
                Select Your Interests
              </h2>
              <p className="mt-2 text-gray-600">
                Choose categories and specific topics that interest you
              </p>
            </div>

            {/* Selected Interests Display */}
            {selectedInterests.length > 0 && (
              <div className="bg-white rounded-xl shadow-md p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  Your Selected Interests
                </h3>
                <div className="space-y-4">
                  {selectedInterests.map((interest, index) => (
                    <div 
                      key={index} 
                      className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 transition-all hover:shadow-md"
                    >
                      <div className="flex justify-between items-start">
                        <div className="space-y-3 flex-grow">
                          <h4 className="font-medium text-lg text-gray-900 capitalize">
                            {interest.category.split('-').join(' ')}
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {interest.topics.map(topic => (
                              <span 
                                key={topic} 
                                className="px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800 border border-blue-200"
                              >
                                {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteInterest(index)}
                          className="ml-4 p-2 text-red-500 hover:bg-red-50 rounded-full transition-colors"
                          title="Remove interest"
                        >
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Interest Selection Form */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="space-y-6">
                {/* Category Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select a Category
                  </label>
                  <div className="relative">
                    <select
                      value={currentCategory}
                      onChange={(e) => {
                        setCurrentCategory(e.target.value);
                        setSelectedTopics([]);
                      }}
                      className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 pl-4 pr-10 py-3 text-base"
                    >
                      <option value="">Choose a category</option>
                      {Object.keys(interestCategories).map(category => (
                        <option key={category} value={category}>
                          {category.split('-').map(word => 
                            word.charAt(0).toUpperCase() + word.slice(1)
                          ).join(' ')}
                        </option>
                      ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Topics Selection */}
                {currentCategory && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <label className="block text-sm font-medium text-gray-700">
                        Select Topics
                      </label>
                      <span className="text-sm text-gray-500">
                        {selectedTopics.length} topics selected
                      </span>
                    </div>
                    <div className="max-h-[400px] overflow-y-auto rounded-lg border border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 p-4">
                        {interestCategories[currentCategory as keyof typeof interestCategories].map(topic => (
                          <label 
                            key={topic} 
                            className={`
                              flex items-center p-3 rounded-lg cursor-pointer transition-all
                              ${selectedTopics.includes(topic) 
                                ? 'bg-blue-50 border-blue-200 shadow-sm' 
                                : 'bg-gray-50 hover:bg-gray-100 border-transparent'}
                              border
                            `}
                          >
                            <input
                              type="checkbox"
                              checked={selectedTopics.includes(topic)}
                              onChange={() => handleTopicToggle(topic)}
                              className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                            />
                            <span className="ml-3 text-sm text-gray-900">{topic}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={handleAddInterest}
                      disabled={!currentCategory || selectedTopics.length === 0}
                      className="w-full mt-4 px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      Add Selected Topics
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="flex gap-4 mt-8">
              <button
                type="button"
                onClick={handleBack}
                className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-base font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={isLoading || selectedInterests.length === 0}
                className={`
                  flex-1 px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white
                  ${isLoading || selectedInterests.length === 0
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500'}
                  transition-colors
                `}
              >
                {isLoading ? 'Creating account...' : 'Create account'}
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      {error && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 text-red-600 text-sm text-center bg-red-50 px-4 py-2 rounded-md">
          {error}
        </div>
      )}
      {renderStepContent()}
    </div>
  );
} 