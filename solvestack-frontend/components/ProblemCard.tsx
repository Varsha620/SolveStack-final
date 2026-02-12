
import React from 'react';
import { Problem, Difficulty } from '../types';
import { PLATFORM_ICONS, DIFFICULTY_COLORS } from '../constants';
import { Heart, Users, ExternalLink, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';

interface ProblemCardProps {
  problem: Problem;
}

const ProblemCard: React.FC<ProblemCardProps> = ({ problem }) => {
  const { isAuthenticated, refreshUser } = useAuth();
  // Note: ProblemCard is used in Dashboard which is under AuthProvider (App.tsx)

  // We need local state to track interest if the backend doesn't return "isInterested" for the user yet
  const [interested, setInterested] = React.useState(problem.isInterested || false);
  const [count, setCount] = React.useState(problem.interestedCount);
  const [loadingInterest, setLoadingInterest] = React.useState(false);

  // Sync state if problem prop changes
  React.useEffect(() => {
    setInterested(problem.isInterested || false);
    setCount(problem.interestedCount);
  }, [problem.isInterested, problem.interestedCount]);

  const handleToggleInterest = async (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent Link navigation
    e.stopPropagation();

    if (!isAuthenticated) {
      // Redirect to login or show alert
      if (confirm("You need to be logged in to track interests. Go to login?")) {
        window.location.href = '#/login';
      }
      return;
    }

    if (loadingInterest) return;
    setLoadingInterest(true);

    try {
      if (interested) {
        const newCount = await apiService.removeInterest(problem.id);
        if (newCount !== null) {
          setInterested(false);
          setCount(newCount);
          refreshUser();
        }
      } else {
        const newCount = await apiService.toggleInterest(problem.id);
        if (newCount !== null) {
          setInterested(true);
          setCount(newCount);
          refreshUser();
        }
      }
    } catch (error) {
      console.error("Failed to toggle interest", error);
    } finally {
      setLoadingInterest(false);
    }
  };

  return (
    <div className="group relative bg-[#090909] border border-white/5 rounded-xl p-5 hover:border-white/20 transition-all duration-300 hover:shadow-[0_0_20px_rgba(255,255,255,0.05)]">
      <div className="flex justify-between items-start mb-4">
        <div className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${DIFFICULTY_COLORS[problem.difficulty]}`}>
          {problem.difficulty}
        </div>
        <div className="flex items-center gap-2 opacity-60 group-hover:opacity-100 transition-opacity">
          {PLATFORM_ICONS[problem.source]}
          <span className="text-[11px] font-medium">{problem.source}</span>
        </div>
      </div>

      <Link to={`/problem/${problem.id}`} className="block group/title">
        <h3 className="text-lg font-semibold text-white/90 group-hover/title:text-white transition-colors mb-2 line-clamp-2 flex items-center gap-1">
          {problem.title}
          <ArrowUpRight className="w-4 h-4 opacity-0 group-hover/title:opacity-100 -translate-x-1 group-hover/title:translate-x-0 transition-all" />
        </h3>
      </Link>

      <p className="text-sm text-white/50 mb-4 line-clamp-3 leading-relaxed">
        {problem.description}
      </p>

      <div className="flex flex-wrap gap-1.5 mb-6">
        {problem.techStack.slice(0, 4).map((tech) => (
          <span key={tech} className="px-2 py-0.5 bg-white/5 rounded-full text-[11px] font-medium text-white/70">
            {tech}
          </span>
        ))}
        {problem.techStack.length > 4 && (
          <span className="text-[11px] text-white/30 flex items-center">+{problem.techStack.length - 4}</span>
        )}
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-white/5">
        <div className="flex items-center gap-4">
          <button
            onClick={handleToggleInterest}
            className={`flex items-center gap-1.5 transition-colors text-xs font-medium ${interested ? 'text-red-500 hover:text-red-400' : 'text-white/40 hover:text-red-400'}`}
          >
            <Heart className={`w-4 h-4 ${interested ? 'fill-current' : ''}`} />
            {count}
          </button>
          <button className="flex items-center gap-1.5 text-white/40 hover:text-cyan-400 transition-colors text-xs font-medium">
            <Users className="w-4 h-4" />
            {problem.collaboratorsCount}
          </button>
        </div>
        <a
          href={problem.sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 text-white/40 hover:text-white hover:bg-white/5 rounded-lg transition-all"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>
    </div>
  );
};

export default ProblemCard;
