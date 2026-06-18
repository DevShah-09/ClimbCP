import { useEffect, useState } from 'react';
import { Compass, Sparkles, Award, Target, HelpCircle, BrainCircuit } from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { useAnalytics } from '../hooks/AnalyticsContext';
import { conceptsApi, embeddingsApi } from '../services/api';
import { LoadingSpinner, ErrorState } from '../components/UIStates';
import ProblemDetailsModal from '../components/ProblemDetailsModal';

export default function LearningMap() {
  const { handle } = useAnalytics();
  const [concepts, setConcepts] = useState([]);
  const [weakConcepts, setWeakConcepts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // ML Pipeline Initialization States
  const [initializing, setInitializing] = useState(false);
  const [initStep, setInitStep] = useState(1);
  const [initMessage, setInitMessage] = useState('');

  // Modal State
  const [selectedProblem, setSelectedProblem] = useState(null);

  const fetchConcepts = () => {
    if (!handle) return;
    setLoading(true);
    conceptsApi.getConcepts(handle)
      .then((data) => {
        setConcepts(data.all_concepts ?? []);
        setWeakConcepts(data.weak_concepts ?? []);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        // If it's a 404/500, it might mean the database has no embeddings/clusters generated yet
        setError(err.message || 'Failed to load concept map.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchConcepts();
  }, [handle]);

  const handleInitializeML = async () => {
    setInitializing(true);
    setError(null);
    try {
      // Step 1: Generate problem embeddings
      setInitStep(1);
      setInitMessage('Step 1/3: Vectorizing Codeforces problems into 384-dimensional space...');
      await embeddingsApi.generateProblems();

      // Step 2: Generate user embedding vector
      setInitStep(2);
      setInitMessage('Step 2/3: Formulating user CP performance vector (128 dimensions)...');
      await embeddingsApi.generateUser(handle);

      // Step 3: Fetch concepts which triggers clustering automatically on backend if needed
      setInitStep(3);
      setInitMessage('Step 3/3: Running KMeans clustering to map custom concept categories...');
      
      const data = await conceptsApi.getConcepts(handle);
      setConcepts(data.all_concepts ?? []);
      setWeakConcepts(data.weak_concepts ?? []);
      setInitializing(false);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Initialization failed. Check if server is online.');
      setInitializing(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Scanning semantic concepts mapping..." />;
  }

  if (initializing) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center px-4 space-y-6">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-accent/20 border-t-accent animate-spin" />
          <BrainCircuit size={28} className="absolute inset-0 m-auto text-accent animate-pulse" />
        </div>
        <div className="space-y-2 max-w-md">
          <h3 className="font-kalam font-bold text-xl text-white">Initializing climbCP ML Layer</h3>
          <p className="text-sm text-text-muted">{initMessage}</p>
        </div>
      </div>
    );
  }

  // If no concepts are generated yet, show the ML Initializer View
  if (error || concepts.length === 0) {
    return (
      <div className="space-y-6 py-6 animate-fade-in pb-8">
        <div>
          <p className="text-text-muted text-sm mb-1">Semantic Intelligence</p>
          <h1 className="font-kalam font-bold text-3xl text-white">Semantic Learning Map</h1>
        </div>

        <div className="glass-card p-8 text-center max-w-xl mx-auto border-accent/20 space-y-6">
          <div className="w-14 h-14 rounded-full bg-accent/10 flex items-center justify-center mx-auto border border-accent/25">
            <BrainCircuit size={28} className="text-accent" />
          </div>

          <div className="space-y-2">
            <h3 className="font-semibold text-lg text-white">Machine Learning Models Uninitialized</h3>
            <p className="text-sm text-text-muted">
              ClimbCP uses vector embeddings to map your competitive programming capabilities. Initialize the semantic layer to calculate concept clusters and peer similarity.
            </p>
          </div>

          <button
            onClick={handleInitializeML}
            className="px-6 py-3 rounded-xl bg-accent hover:bg-accent-hover text-white text-sm font-semibold transition-all shadow-lg shadow-accent/20 flex items-center gap-2 mx-auto cursor-pointer"
          >
            <Sparkles size={16} />
            Initialize Semantic ML Layer
          </button>
          
          {error && (
            <p className="text-xs text-red-400 mt-2 bg-red-500/10 p-2 rounded-lg border border-red-500/15">
              Error details: {error}
            </p>
          )}
        </div>
      </div>
    );
  }

  // Prepare radar chart data
  const radarData = concepts.slice(0, 7).map(c => ({
    subject: c.concept,
    A: c.mastery,
    fullMark: 100,
  }));

  const getMasteryColor = (score) => {
    if (score < 60) return 'text-red-400 border-red-500/20 bg-red-500/5';
    if (score < 75) return 'text-amber-400 border-amber-500/20 bg-amber-500/5';
    return 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5';
  };

  const getProgressColor = (score) => {
    if (score < 60) return 'bg-red-500';
    if (score < 75) return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-text-muted text-sm mb-1">Semantic Intelligence</p>
          <h1 className="font-kalam font-bold text-3xl text-white">Semantic Learning Map</h1>
        </div>

        <button
          onClick={handleInitializeML}
          className="px-4 py-2 rounded-lg bg-surface/80 border border-border text-xs text-text-secondary hover:text-white hover:border-accent/40 transition-all cursor-pointer flex items-center gap-1.5"
        >
          <Sparkles size={13} className="text-accent" />
          Re-run ML Pipeline
        </button>
      </div>

      {/* Radar Chart & High-Level Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-6 flex flex-col justify-between">
          <div>
            <h3 className="font-semibold text-white mb-1 flex items-center gap-1.5">
              <Compass size={16} className="text-accent" />
              Concept Mastery Radar
            </h3>
            <p className="text-xs text-text-muted mb-4">
              Your mastery across 7 major semantic concept clusters generated by KMeans clustering.
            </p>
          </div>

          <div className="h-72 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                <PolarGrid stroke="#2c2c35" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#475569' }} />
                <Radar
                  name="Mastery"
                  dataKey="A"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.15}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Weakness summary panel */}
        <div className="glass-card p-6 flex flex-col justify-between border-red-500/10 bg-gradient-to-b from-red-500/5 to-transparent">
          <div className="space-y-4">
            <h3 className="font-semibold text-white flex items-center gap-1.5">
              <Target size={16} className="text-red-400" />
              Priority Focus Concepts
            </h3>
            <p className="text-xs text-text-muted">
              These concepts represent your largest semantic skill gaps. Solving recommended problems in these areas will yield the fastest rating growth.
            </p>

            <div className="space-y-2.5 max-h-[200px] overflow-y-auto pr-1">
              {weakConcepts.slice(0, 4).map((c, i) => (
                <div key={i} className="flex items-center justify-between p-2.5 rounded-lg bg-surface border border-border/60">
                  <span className="text-xs font-medium text-white">{c.concept}</span>
                  <span className="text-xs font-semibold font-mono text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/15">
                    {c.mastery}% Mastery
                  </span>
                </div>
              ))}
              {weakConcepts.length === 0 && (
                <p className="text-xs text-emerald-400 text-center py-6">All concepts mastered above 60%! Excellent job!</p>
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-border/80">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-accent/15 flex items-center justify-center">
                <Award size={14} className="text-accent" />
              </div>
              <div>
                <p className="text-xs font-semibold text-white">Semantic Mastery</p>
                <p className="text-[10px] text-text-muted">Grounded in vector similarity & failure tracking</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Grid of Concept Cards */}
      <div className="space-y-4">
        <h3 className="font-semibold text-white text-lg">Detailed Concept Breakdown</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {concepts.map((c, idx) => (
            <div 
              key={c.cluster_id || idx}
              className={`glass-card p-5 border flex flex-col justify-between gap-4 transition-all hover:-translate-y-0.5 ${getMasteryColor(c.mastery)}`}
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <h4 className="font-kalam font-bold text-lg text-white leading-tight">{c.concept}</h4>
                  <span className="text-xs font-bold font-mono px-2.5 py-0.5 rounded-full border bg-surface/50">
                    {c.mastery}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full h-1.5 rounded-full bg-border/40 overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${getProgressColor(c.mastery)}`}
                    style={{ width: `${c.mastery}%` }}
                  />
                </div>

                <div className="flex items-center gap-4 text-[10px] text-text-muted font-medium">
                  <p>Solved: <span className="text-white">{c.solved}</span></p>
                  <p>Attempted: <span className="text-white">{c.attempted}</span></p>
                </div>
              </div>

              {/* Recommended Problems inside cluster */}
              <div className="pt-3 border-t border-border/60 space-y-2">
                <p className="text-[10px] font-semibold text-white uppercase tracking-wider">Concept Recommendations</p>
                
                {c.recommendations?.length === 0 ? (
                  <p className="text-[10px] text-text-muted">No unsolved recommendations left!</p>
                ) : (
                  <div className="space-y-1.5">
                    {c.recommendations?.map((rec, i) => (
                      <div 
                        key={rec.problem_id || i}
                        onClick={() => setSelectedProblem({
                          id: rec.problem_id,
                          name: rec.name,
                          rating: rec.rating,
                          problem_code: rec.problem_code
                        })}
                        className="flex items-center justify-between p-2 rounded-lg bg-surface/40 border border-border/40 hover:border-accent/40 hover:bg-surface/80 transition-all cursor-pointer group"
                      >
                        <span className="text-[11px] text-text-secondary group-hover:text-white truncate max-w-[120px] font-medium leading-tight">
                          {rec.name}
                        </span>
                        <span className="text-[10px] font-semibold font-mono text-accent">
                          *{rec.rating}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Details & Similar Problems Modal */}
      {selectedProblem && (
        <ProblemDetailsModal
          isOpen={!!selectedProblem}
          onClose={() => setSelectedProblem(null)}
          problemId={selectedProblem.id}
          problemName={selectedProblem.name}
          rating={selectedProblem.rating}
          problemCode={selectedProblem.problem_code}
        />
      )}
    </div>
  );
}
