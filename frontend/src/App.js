import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "sonner";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Progress } from "./components/ui/progress";
import { Badge } from "./components/ui/badge";
import { Separator } from "./components/ui/separator";
import { GraduationCap, MapPin, Clock, DollarSign, FileText, Sparkles, CheckCircle, ArrowRight, User, Mail, Lock, Globe } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile`);
      setUser(response.data.user);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user);
      
      // Force navigation to dashboard
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 100);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (email, password, phone) => {
    try {
      const response = await axios.post(`${API}/auth/register`, { email, password, phone });
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user);
      
      // Force navigation to dashboard
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 100);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100">
        <div className="animate-pulse text-center">
          <GraduationCap className="w-12 h-12 mx-auto mb-4 text-amber-600" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

// Landing Page
const LandingPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-red-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <GraduationCap className="w-8 h-8 text-amber-600" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-amber-600 to-orange-600 bg-clip-text text-transparent">
                Orienta
              </h1>
            </div>
            <div className="flex space-x-4">
              <Button variant="outline" asChild>
                <a href="/login">Login</a>
              </Button>
              <Button asChild>
                <a href="/register">Get Started</a>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <div className="mb-8">
            <Badge className="mb-4 bg-amber-100 text-amber-800 hover:bg-amber-200">
              <Globe className="w-3 h-3 mr-1" />
              South African Education Guide
            </Badge>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Find Your Perfect
            <span className="bg-gradient-to-r from-amber-600 to-orange-600 bg-clip-text text-transparent block">
              Study Path
            </span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
            Get personalized study recommendations, funding options, and a 90-day action plan 
            tailored for South African Grade 11 & 12 learners in just 10-15 minutes.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Button size="lg" className="text-lg px-8 py-6" asChild>
              <a href="/register">
                Start Your Journey
                <ArrowRight className="ml-2 w-5 h-5" />
              </a>
            </Button>
            <Button variant="outline" size="lg" className="text-lg px-8 py-6" asChild>
              <a href="#how-it-works">Learn More</a>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="how-it-works" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">How Orienta Works</h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          <Card className="text-center p-6 border-0 bg-white/60 backdrop-blur-sm">
            <CardContent className="pt-6">
              <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="w-6 h-6 text-amber-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Quick Assessment</h3>
              <p className="text-gray-600">
                Complete our smart intake in 10-15 minutes. We'll ask about your grades, interests, and goals.
              </p>
            </CardContent>
          </Card>

          <Card className="text-center p-6 border-0 bg-white/60 backdrop-blur-sm">
            <CardContent className="pt-6">
              <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Smart Matching</h3>
              <p className="text-gray-600">
                Get three personalized study pathways with funding options that match your profile.
              </p>
            </CardContent>
          </Card>

          <Card className="text-center p-6 border-0 bg-white/60 backdrop-blur-sm">
            <CardContent className="pt-6">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Action Plan</h3>
              <p className="text-gray-600">
                Receive a detailed 90-day checklist with deadlines and links to get you started.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Simple, Transparent Pricing</h2>
          <p className="text-gray-600">One-time payment per academic season</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-2xl mx-auto">
          <Card className="p-6 border-2 border-amber-200">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Learner Plan</CardTitle>
              <div className="text-4xl font-bold text-amber-600 mt-2">R79</div>
              <p className="text-gray-600">Perfect for most students</p>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-center"><CheckCircle className="w-4 h-4 text-green-600 mr-2" />Complete intake assessment</li>
                <li className="flex items-center"><CheckCircle className="w-4 h-4 text-green-600 mr-2" />3 personalized pathways</li>
                <li className="flex items-center"><CheckCircle className="w-4 h-4 text-green-600 mr-2" />Funding recommendations</li>
                <li className="flex items-center"><CheckCircle className="w-4 h-4 text-green-600 mr-2" />90-day action plan</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="p-6 border-2 border-orange-200">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Premium Plan</CardTitle>
              <div className="text-4xl font-bold text-orange-600 mt-2">R129</div>
              <p className="text-gray-600">Enhanced support</p>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-center"><CheckCircle className="w-4 h-4 text-green-600 mr-2" />Everything in Learner Plan</li>
                <li className="flex items-center"><CheckCircle className="w-4 h-4 text-green-600 mr-2" />Human review included</li>
                <li className="flex items-center"><CheckCircle className="w-4 h-4 text-green-600 mr-2" />Priority support</li>
                <li className="flex items-center"><CheckCircle className="w-4 h-4 text-green-600 mr-2" />Additional resources</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center justify-center">
            <GraduationCap className="w-6 h-6 mr-2" />
            <span className="text-xl font-semibold">Orienta</span>
          </div>
          <p className="text-center text-gray-400 mt-4">
            Guiding South African learners to their perfect study path
          </p>
        </div>
      </footer>
    </div>
  );
};

// Auth Pages
const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const result = await login(email, password);
    if (result.success) {
      toast.success('Login successful!');
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center mb-4">
            <GraduationCap className="w-8 h-8 text-amber-600" />
          </div>
          <CardTitle className="text-2xl">Welcome Back</CardTitle>
          <p className="text-gray-600">Sign in to continue your journey</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-9"
                  placeholder="your@email.com"
                  required
                />
              </div>
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-9"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Don't have an account?{' '}
              <a href="/register" className="text-amber-600 hover:underline">
                Sign up
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const RegisterPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const result = await register(email, password, phone);
    if (result.success) {
      toast.success('Registration successful!');
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center mb-4">
            <GraduationCap className="w-8 h-8 text-amber-600" />
          </div>
          <CardTitle className="text-2xl">Start Your Journey</CardTitle>
          <p className="text-gray-600">Create your account to get started</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email Address</Label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-9"
                  placeholder="your@email.com"
                  required
                />
              </div>
            </div>
            <div>
              <Label htmlFor="phone">Phone Number</Label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  id="phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="pl-9"
                  placeholder="+27 123 456 7890"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-9"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Creating Account...' : 'Create Account'}
            </Button>
          </form>
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Already have an account?{' '}
              <a href="/login" className="text-amber-600 hover:underline">
                Sign in
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Dashboard Layout
const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <GraduationCap className="w-8 h-8 text-amber-600" />
              <h1 className="text-2xl font-bold text-gray-900">Orienta</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user?.email}</span>
              <Button variant="outline" onClick={logout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [intakeStatus, setIntakeStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile`);
      if (response.data.profile) {
        setIntakeStatus(response.data.profile);
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <div className="animate-pulse">Loading...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Your Dashboard</h2>
          <p className="text-gray-600 mt-2">Track your progress and next steps</p>
        </div>

        {!intakeStatus?.intake_completed ? (
          <Card className="p-8 text-center">
            <CardContent>
              <FileText className="w-16 h-16 mx-auto mb-4 text-amber-600" />
              <h3 className="text-2xl font-semibold mb-2">Ready to Start?</h3>
              <p className="text-gray-600 mb-6">
                Complete our 10-15 minute assessment to get personalized study recommendations.
              </p>
              <Button size="lg" asChild>
                <a href="/intake">Start Assessment</a>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                  Assessment Complete
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  You've completed your intake assessment. Ready to unlock your pathways?
                </p>
                <Button asChild>
                  <a href="/pathways">View Pathways</a>
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Sparkles className="w-5 h-5 mr-2 text-amber-600" />
                  Next Steps
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Review your pathway matches</li>
                  <li>• Explore funding options</li>
                  <li>• Download your action plan</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

// Main App Component
function App() {
  return (
    <div className="App">
      <Toaster position="top-right" />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<AppRoutes />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/intake" element={<ProtectedRoute><IntakePage /></ProtectedRoute>} />
            <Route path="/pathways" element={<ProtectedRoute><PathwaysPage /></ProtectedRoute>} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

const AppRoutes = () => {
  const { user } = useAuth();
  
  // Check for payment success
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    if (sessionId) {
      toast.success('Payment successful! Your access has been unlocked.');
      // Clear the URL parameter
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);
  
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }
  return <LandingPage />;
};

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

// Intake Page Component
const IntakePage = () => {
  const [questions, setQuestions] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchQuestions();
  }, []);

  const fetchQuestions = async () => {
    try {
      const response = await axios.get(`${API}/intake/questions`);
      setQuestions(response.data.questions);
      
      // Start intake session
      await axios.post(`${API}/intake/start`);
    } catch (error) {
      toast.error('Failed to load questions');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async (answer) => {
    const question = questions[currentStep];
    setAnswers(prev => ({ ...prev, [question.id]: answer }));
    
    setSubmitting(true);
    try {
      const response = await axios.post(`${API}/intake/answer`, null, {
        params: { question_id: question.id, answer: JSON.stringify(answer) }
      });
      
      if (response.data.session.completed) {
        toast.success('Assessment completed!');
        window.location.href = '/pathways';
      } else {
        setCurrentStep(prev => prev + 1);
      }
    } catch (error) {
      toast.error('Failed to save answer');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">Loading questions...</div>
      </DashboardLayout>
    );
  }

  const currentQuestion = questions[currentStep];
  const progress = ((currentStep + 1) / questions.length) * 100;

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Assessment</h2>
            <span className="text-sm text-gray-500">
              {currentStep + 1} of {questions.length}
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        <Card className="p-8">
          <CardContent>
            <h3 className="text-xl font-semibold mb-6">{currentQuestion?.text}</h3>
            
            <QuestionInput 
              question={currentQuestion}
              onAnswer={handleAnswer}
              disabled={submitting}
            />
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

const QuestionInput = ({ question, onAnswer, disabled }) => {
  const [value, setValue] = useState('');
  
  const handleSubmit = () => {
    if (!value) return;
    onAnswer(value);
  };

  if (question?.type === 'select') {
    return (
      <div className="space-y-3">
        {question.options?.map((option, index) => (
          <Button
            key={index}
            variant="outline"
            className="w-full text-left justify-start p-4 h-auto"
            onClick={() => onAnswer(option)}
            disabled={disabled}
          >
            {option}
          </Button>
        ))}
      </div>
    );
  }

  if (question?.type === 'multiselect') {
    return (
      <div className="space-y-4">
        {question.options?.map((option, index) => (
          <label key={index} className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              className="rounded border-gray-300"
              onChange={(e) => {
                const currentValues = Array.isArray(value) ? value : [];
                if (e.target.checked) {
                  setValue([...currentValues, option]);
                } else {
                  setValue(currentValues.filter(v => v !== option));
                }
              }}
            />
            <span>{option}</span>
          </label>
        ))}
        <Button 
          onClick={handleSubmit}
          disabled={disabled || !Array.isArray(value) || value.length === 0}
          className="mt-4"
        >
          Continue
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Type your answer..."
        disabled={disabled}
      />
      <Button onClick={handleSubmit} disabled={disabled || !value}>
        Continue
      </Button>
    </div>
  );
};

// Pathways Page
const PathwaysPage = () => {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPreview();
  }, []);

  const fetchPreview = async () => {
    try {
      const response = await axios.get(`${API}/pathways/preview`);
      setPreview(response.data);
    } catch (error) {
      console.error('Failed to fetch preview:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async (planType, gateway = 'paystack') => {
    try {
      const response = await axios.post(`${API}/payments/create-checkout`, {
        plan_type: planType,
        gateway: gateway
      });
      
      if (response.data.checkout_url) {
        // Store payment info for verification
        localStorage.setItem('pending_payment', JSON.stringify({
          reference: response.data.reference || response.data.session_id,
          gateway: response.data.gateway,
          plan_type: planType
        }));
        
        window.location.href = response.data.checkout_url;
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Payment failed');
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">Loading pathways...</div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Your Study Pathways</h2>
          <p className="text-gray-600">Unlock personalized recommendations</p>
        </div>

        {preview && (
          <Card className="p-6">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>{preview.programme?.title}</span>
                <Badge variant="outline">Preview</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div className="flex items-center">
                  <GraduationCap className="w-4 h-4 mr-2 text-gray-500" />
                  {preview.institution?.name}
                </div>
                <div className="flex items-center">
                  <MapPin className="w-4 h-4 mr-2 text-gray-500" />
                  {preview.programme?.city}, {preview.programme?.province}
                </div>
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-2 text-gray-500" />
                  {preview.programme?.duration_months} months
                </div>
                <div className="flex items-center">
                  <DollarSign className="w-4 h-4 mr-2 text-gray-500" />
                  R{preview.programme?.total_estimated_cost?.toLocaleString()}
                </div>
              </div>
              
              <Separator />
              
              <div className="bg-amber-50 p-4 rounded-lg text-center">
                <h3 className="font-semibold mb-2">This is just a preview!</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Unlock your full pathway analysis with 3 personalized options, funding recommendations, and a 90-day action plan.
                </p>
                
                <div className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <Button 
                      onClick={() => handlePayment('learner', 'paystack')}
                      className="w-full bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700"
                    >
                      Pay with Paystack R79
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => handlePayment('premium', 'paystack')}
                      className="w-full border-green-600 text-green-600 hover:bg-green-50"
                    >
                      Premium R129
                    </Button>
                  </div>
                  
                  <div className="text-center">
                    <div className="relative">
                      <Separator className="my-4" />
                      <span className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-amber-50 px-3 text-sm text-gray-500">
                        or pay with
                      </span>
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    <Button 
                      onClick={() => handlePayment('learner', 'stripe')}
                      className="w-full bg-purple-600 hover:bg-purple-700"
                    >
                      Pay with Stripe R79
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => handlePayment('premium', 'stripe')}
                      className="w-full border-purple-600 text-purple-600 hover:bg-purple-50"
                    >
                      Premium R129 (Stripe)
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

export default App;