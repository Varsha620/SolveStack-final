
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Problem, SolutionType } from '../types';
import { apiService } from '../services/api';
import {
  ArrowLeft,
  ExternalLink,
  MessageSquare,
  Users,
  Heart,
  Cpu,
  Code,
  Layers,
  Sparkles,
  Zap,
  Loader2,
  BarChart3
} from 'lucide-react';
import { GoogleGenAI, Type } from "@google/genai";
import { useAuth } from '../contexts/AuthContext';
import InferenceOverlay from '../components/InferenceOverlay';

const ProblemDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated, refreshUser } = useAuth();
  const [problem, setProblem] = useState<Problem | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiInsight, setAiInsight] = useState<string>('');
  const [loadingAi, setLoadingAi] = useState(false);

  const [interested, setInterested] = useState(false);
  const [count, setCount] = useState(0);
  const [loadingInterest, setLoadingInterest] = useState(false);

  // Expo Showmanship States
  const [isOverlayOpen, setIsOverlayOpen] = useState(false);
  const [overlayLoading, setOverlayLoading] = useState(false);
  const [explanationData, setExplanationData] = useState<any>(null);
  const [prototypeData, setPrototypeData] = useState<any>(null);

  useEffect(() => {
    const fetch = async () => {
      if (!id) return;
      const data = await apiService.getProblemById(id);
      if (data) {
        setProblem(data);
        setInterested(data.isInterested || false);
        setCount(data.interestedCount || 0);
      }
      setLoading(false);
    };
    fetch();
  }, [id]);

  const handleToggleInterest = async () => {
    if (!isAuthenticated) {
      alert("Please sign in to favorite problems");
      return;
    }
    if (!problem || loadingInterest) return;

    setLoadingInterest(true);
    try {
      if (interested) {
        const success = await apiService.removeInterest(problem.id);
        if (success) {
          setInterested(false);
          setCount(prev => prev - 1);
          refreshUser();
        }
      } else {
        const success = await apiService.toggleInterest(problem.id);
        if (success) {
          setInterested(true);
          setCount(prev => prev + 1);
          refreshUser();
        }
      }
    } catch (error) {
      console.error("Failed to toggle interest", error);
    } finally {
      setLoadingInterest(false);
    }
  };

  const handleShowIntelligence = async (mode: 'explain' | 'prototype') => {
    setIsOverlayOpen(true);
    if (mode === 'explain' && explanationData) return;
    if (mode === 'prototype' && prototypeData) return;

    setOverlayLoading(true);
    try {
      const [expl, proto] = await Promise.all([
        explanationData ? Promise.resolve(explanationData) : apiService.getExplanation(problem?.id || ''),
        mode === 'prototype' ? apiService.getPrototype(problem?.id || '') : Promise.resolve(prototypeData)
      ]);
      setExplanationData(expl);
      if (proto) setPrototypeData(proto);
    } catch (error) {
      console.error("Failed to fetch intelligence", error);
    } finally {
      setOverlayLoading(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-white/10 border-t-white rounded-full animate-spin" />
    </div>
  );

  if (!problem) return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-6 text-center">
      <h1 className="text-2xl font-bold mb-4">Problem not found</h1>
      <Link to="/dashboard" className="px-6 py-2 bg-white text-black rounded-full font-bold">Back to Shelf</Link>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Top Nav */}
      <nav className="sticky top-0 z-20 border-b border-white/5 bg-black/80 backdrop-blur-md">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-2 text-white/50 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Shelf</span>
          </Link>
          <div className="flex items-center gap-4">
            <button
              onClick={handleToggleInterest}
              disabled={loadingInterest}
              className={`p-2 transition-colors ${interested ? 'text-red-500' : 'text-white/50 hover:text-white'}`}
            >
              {loadingInterest ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Heart className={`w-5 h-5 ${interested ? 'fill-current' : ''}`} />
              )}
            </button>
            <button className="px-5 py-2 bg-cyan-500 text-black font-bold text-sm rounded-full hover:bg-cyan-400 transition-all">
              Request Collaboration
            </button>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-12 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Left Column: Brief */}
          <div className="lg:col-span-2 space-y-12">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className={`px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border border-white/10 bg-white/5`}>
                  {problem.difficulty}
                </span>
                <span className="text-white/30 text-xs flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Found {new Date(problem.createdAt).toLocaleDateString()}
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-black mb-6 leading-tight">
                {problem.title}
              </h1>
              <div className="flex flex-wrap gap-2 mb-8">
                {problem.techStack.map(tech => (
                  <span key={tech} className="px-4 py-1.5 bg-white/5 rounded-lg border border-white/5 text-sm font-medium text-white/70">
                    {tech}
                  </span>
                ))}
              </div>
            </div>

            <section className="space-y-6">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-widest text-white/30 mb-4 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Context
                </h3>
                <p className="text-xl text-white/80 leading-relaxed font-light">
                  {problem.humanExplanation}
                </p>
              </div>

              <div className="p-8 rounded-2xl bg-[#090909] border border-white/5">
                <h3 className="text-sm font-bold uppercase tracking-widest text-white/30 mb-4">Original Problem Statement</h3>
                <p className="text-white/50 leading-relaxed italic">
                  "{problem.description}"
                </p>
                <a
                  href={problem.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-6 inline-flex items-center gap-2 text-cyan-500 text-sm font-bold group"
                >
                  View Original Post on {problem.source}
                  <ExternalLink className="w-4 h-4 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                </a>
              </div>
            </section>

            {/* Smart Roadmap (Gemini) */}
            <section className="p-8 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-transparent border border-cyan-500/20">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-cyan-400" />
                  AI Discovery & Execution
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => handleShowIntelligence('explain')}
                  className="p-6 bg-white/5 hover:bg-white/10 border border-white/5 rounded-2xl text-left transition-all group"
                >
                  <BarChart3 className="w-6 h-6 text-cyan-400 mb-4 group-hover:scale-110 transition-transform" />
                  <h4 className="font-bold mb-1">Explain Intelligence</h4>
                  <p className="text-xs text-white/40">View the heuristic breakdown of why this problem ranks for high impact.</p>
                </button>

                {/* Hiding Launch Prototype for now due to Quota issues */}
                {/* 
                <button
                  onClick={() => handleShowIntelligence('prototype')}
                  className="p-6 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 rounded-2xl text-left transition-all group"
                >
                  <Zap className="w-6 h-6 text-cyan-400 mb-4 group-hover:scale-110 transition-transform" />
                  <h4 className="font-bold mb-1 text-cyan-400">Launch Prototype</h4>
                  <p className="text-xs text-cyan-400/40">Generate a custom 3-step technical roadmap for MVP implementation.</p>
                </button>
                */}
              </div>
            </section>
          </div>

          {/* Right Column: Stats & Meta */}
          <div className="space-y-8">
            <div className="p-6 rounded-2xl bg-[#090909] border border-white/5">
              <h3 className="text-xs font-bold uppercase tracking-widest text-white/30 mb-6">Metrics</h3>
              <div className="space-y-6">
                <button
                  onClick={handleToggleInterest}
                  disabled={loadingInterest}
                  className="w-full flex items-center justify-between group"
                >
                  <span className={`text-sm flex items-center gap-2 transition-colors ${interested ? 'text-red-500' : 'text-white/50 group-hover:text-white'}`}>
                    <Heart className={`w-4 h-4 ${interested ? 'fill-current' : ''}`} />
                    {interested ? 'Interested' : 'Mark as Interested'}
                  </span>
                  <span className="font-bold">{count}</span>
                </button>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/50 flex items-center gap-2">
                    <Users className="w-4 h-4" /> Squad Members
                  </span>
                  <span className="font-bold">{problem.collaboratorsCount} / 5</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/50 flex items-center gap-2">
                    <Layers className="w-4 h-4" /> Solution Type
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${problem.solutionType === SolutionType.SOFTWARE ? 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20' :
                    problem.solutionType === SolutionType.HARDWARE ? 'bg-orange-500/10 text-orange-500 border-orange-500/20' :
                      'bg-purple-500/10 text-purple-500 border-purple-500/20'
                    }`}>
                    {problem.solutionType}
                  </span>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-[#090909] border border-white/5">
              <h3 className="text-xs font-bold uppercase tracking-widest text-white/30 mb-6">Recommended Skills</h3>
              <div className="flex flex-wrap gap-2">
                {['System Design', 'API Integration', 'UI/UX', ...problem.techStack.slice(0, 2)].map(skill => (
                  <span key={skill} className="px-3 py-1 bg-white/5 rounded-full text-xs text-white/40">
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-1 border border-white/5 rounded-2xl bg-gradient-to-t from-white/5 to-transparent overflow-hidden">
              <div className="bg-[#090909] rounded-[14px] p-6 text-center">
                <Zap className="w-8 h-8 text-yellow-500 mx-auto mb-4" />
                <h4 className="font-bold mb-2">Build this Project</h4>
                <p className="text-xs text-white/40 mb-6">Ready to solve this? Click below to find or start a collaboration group.</p>
                <button className="w-full py-3 bg-white text-black font-bold rounded-xl hover:bg-white/90 transition-all">
                  Start Squad
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>

      <InferenceOverlay
        isOpen={isOverlayOpen}
        onClose={() => setIsOverlayOpen(false)}
        problemTitle={problem.title}
        explanationData={explanationData}
        prototypeData={prototypeData}
        loading={overlayLoading}
      />
    </div>
  );
};

// Helper for clock since Lucide clock was used but not imported in detail
const Clock: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
);

export default ProblemDetail;
