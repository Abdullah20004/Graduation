import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Search, AlertCircle, Shield, Sword, Play, Square, Trophy, Clock, Target, Zap, CheckCircle, XCircle, AlertTriangle, Loader, Terminal, Activity, Lock, Unlock, Folder, ChevronDown, ChevronRight } from 'lucide-react';

const API_URL = `${window.location.protocol}//${window.location.hostname}:5000`;

// =============================================================================
// AI CONTROL COMPONENT
// =============================================================================

const AIControlPanel = ({ enabled, setEnabled, onStep, lastLog, aiRole }) => {
  return (
    <div className={`fixed bottom-6 right-6 p-4 rounded-xl border-2 shadow-2xl transition-all z-50 ${enabled
      ? 'bg-slate-900/90 border-purple-500/50 shadow-purple-500/20'
      : 'bg-slate-900/50 border-slate-700/50 grayscale'
      }`}>
      <div className="flex items-center gap-4 mb-3">
        <div className={`p-2 rounded-lg ${enabled ? 'bg-purple-600' : 'bg-slate-700'}`}>
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-bold text-white">AI Opponent ({aiRole})</h3>
          <p className="text-xs text-gray-400">
            {enabled ? 'Active & Thinking...' : 'Offline'}
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer ml-2">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
        </label>
      </div>

      {enabled && lastLog && (
        <div className="bg-black/50 rounded-lg p-3 max-w-sm">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>LATEST ACTION</span>
            <span>{new Date().toLocaleTimeString()}</span>
          </div>
          <div className="font-mono text-sm text-purple-300 break-words">
            {lastLog}
          </div>
        </div>
      )}
    </div>
  );
};

// =============================================================================
// LOG DISPLAY COMPONENTS
// =============================================================================

const ActivityLogPanel = ({ sessionId }) => {
  const [logs, setLogs] = React.useState([]);

  React.useEffect(() => {
    if (!sessionId) return;

    const fetchLogs = async () => {
      try {
        const response = await fetch(`${API_URL}/api/session/${sessionId}/logs/activity?limit=20`);
        const data = await response.json();
        if (data.status === 'success') {
          setLogs(data.logs);
        }
      } catch (err) {
        console.error('Failed to fetch activity logs:', err);
      }
    };

    // Initial fetch
    fetchLogs();
    // Poll every 2 seconds
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const getActionIcon = (actionType) => {
    const icons = {
      'login': '🔐',
      'exploit': '⚔️',
      'patch': '🛡️',
      'scan': '🔍',
      'error': '❌'
    };
    return icons[actionType] || '📝';
  };

  const getActionColor = (actionType, success) => {
    if (!success) return 'text-red-400 bg-red-500/10 border-red-500/30';
    const colors = {
      'login': 'text-blue-400 bg-blue-500/10 border-blue-500/30',
      'exploit': 'text-red-400 bg-red-500/10 border-red-500/30',
      'patch': 'text-green-400 bg-green-500/10 border-green-500/30',
      'scan': 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30'
    };
    return colors[actionType] || 'text-gray-400 bg-gray-500/10 border-gray-500/30';
  };

  return (
    <div className="bg-slate-900/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-4 flex flex-col" style={{ maxHeight: '450px', minHeight: '300px' }}>
      <div className="flex items-center gap-2 mb-3 pb-3 border-b border-slate-700/50 flex-shrink-0">
        <Terminal className="w-5 h-5 text-cyan-400" />
        <h3 className="font-bold text-white">DVWA Activity Log</h3>
        <div className="ml-auto">
          <span className="text-xs text-gray-400">{logs.length} entries</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2 min-h-0">
        {logs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No activity yet</p>
          </div>
        ) : (
          logs.map((log, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border ${getActionColor(log.action_type, log.success)} transition-all hover:scale-[1.01]`}
            >
              <div className="flex items-start gap-2">
                <span className="text-lg">{getActionIcon(log.action_type)}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-gray-400">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="text-xs font-semibold text-cyan-400">
                      {log.location}
                    </span>
                  </div>
                  <p className="text-sm text-gray-200 break-words">{log.description}</p>
                  {log.payload && log.payload !== '<truncated>' && (
                    <p className="text-xs font-mono text-purple-400 mt-1 truncate">
                      Payload: {log.payload}
                    </p>
                  )}
                </div>
                {log.success ? (
                  <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const AIAgentLogPanel = ({ sessionId }) => {
  const [logs, setLogs] = React.useState([]);
  const [currentPage, setCurrentPage] = React.useState(null);

  React.useEffect(() => {
    if (!sessionId) return;

    const fetchLogs = async () => {
      try {
        const response = await fetch(`${API_URL}/api/session/${sessionId}/logs/ai?limit=15`);
        const data = await response.json();
        if (data.status === 'success') {
          setLogs(data.logs);
          // Extract current page from most recent execution log
          const recentExecution = data.logs.find(log => log.stage === 'execution' && log.current_page);
          if (recentExecution) {
            setCurrentPage(recentExecution.current_page);
          }
        }
      } catch (err) {
        console.error('Failed to fetch AI logs:', err);
      }
    };

    // Initial fetch
    fetchLogs();
    // Poll every 2 seconds
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const getStageIcon = (stage) => {
    const icons = {
      'observation': '👁️',
      'decision': '🧠',
      'mapping': '🗺️',
      'execution': '⚡',
      'error': '❌'
    };
    return icons[stage] || '📋';
  };

  const getStageColor = (stage, success) => {
    if (!success && stage !== 'observation') return 'text-red-400 bg-red-500/10 border-red-500/30';
    const colors = {
      'observation': 'text-blue-400 bg-blue-500/10 border-blue-500/30',
      'decision': 'text-purple-400 bg-purple-500/10 border-purple-500/30',
      'mapping': 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
      'execution': 'text-green-400 bg-green-500/10 border-green-500/30',
      'error': 'text-red-400 bg-red-500/10 border-red-500/30'
    };
    return colors[stage] || 'text-gray-400 bg-gray-500/10 border-gray-500/30';
  };

  const getRoleColor = (agentType) => {
    return agentType === 'red' ? 'text-red-400' : 'text-blue-400';
  };

  return (
    <div className="bg-slate-900/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-4 flex flex-col" style={{ maxHeight: '450px', minHeight: '300px' }}>
      <div className="flex items-center gap-2 mb-3 pb-3 border-b border-slate-700/50 flex-shrink-0">
        <Zap className="w-5 h-5 text-purple-400" />
        <h3 className="font-bold text-white">AI Agent Activity</h3>
        {currentPage && (
          <div className="ml-auto">
            <span className="text-xs text-gray-400">Current Page: </span>
            <span className="text-xs font-mono text-cyan-400">{currentPage}</span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2 min-h-0">
        {logs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Zap className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">AI agent inactive</p>
          </div>
        ) : (
          logs.map((log, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border ${getStageColor(log.stage, log.success)} transition-all`}
            >
              <div className="flex items-start gap-2">
                <span className="text-lg">{getStageIcon(log.stage)}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="text-xs font-mono text-gray-400">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span className={`text-xs font-bold ${getRoleColor(log.agent_type)}`}>
                      {log.agent_type?.toUpperCase()}
                    </span>
                    <span className="text-xs font-semibold text-purple-400">
                      {log.stage.toUpperCase()}
                    </span>
                    {log.current_page && (
                      <span className="text-xs font-mono text-cyan-400 truncate">
                        {log.current_page}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-200 break-words">{log.details}</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const PagesPanel = ({ sessionId }) => {
  const [pages, setPages] = React.useState([]);
  const [byCategory, setByCategory] = React.useState({});
  const [summary, setSummary] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    if (!sessionId) return;
    const fetchPages = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_URL}/api/session/${sessionId}/pages`);
        const data = await response.json();
        if (data.status === 'success') {
          setPages(data.pages);
          setByCategory(data.by_category || {});
          setSummary(data.summary);
        }
      } catch (error) {
        console.error('Failed to fetch pages:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchPages();
    const interval = setInterval(fetchPages, 3000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const getStatusColor = (page) => {
    if (page.is_safe) return 'border-green-500/30 bg-green-500/10';
    if (page.exploited_count > 0) return 'border-red-500/50 bg-red-500/10';
    if (page.patched_count > 0 && page.patched_count < page.vulnerability_count) return 'border-yellow-500/50 bg-yellow-500/10';
    return 'border-red-500/30 bg-red-500/10';
  };

  const getStatusIcon = (page) => {
    if (page.is_safe) return <Shield className="w-3 h-3 text-green-400" />;
    if (page.exploited_count > 0) return <AlertCircle className="w-3 h-3 text-red-400" />;
    if (page.patched_count > 0) return <Lock className="w-3 h-3 text-yellow-400" />;
    return <Unlock className="w-3 h-3 text-red-400" />;
  };

  const categoryNames = {
    public: { name: 'Public', icon: '🌐' },
    catalog: { name: 'Catalog', icon: '🛍️' },
    auth: { name: 'Auth', icon: '🔐' },
    shopping: { name: 'Shopping', icon: '🛒' },
    account: { name: 'Account', icon: '👤' },
    admin: { name: 'Admin', icon: '⚙️' }
  };

  if (loading && pages.length === 0) {
    return <div className="flex items-center justify-center p-6"><Loader className="w-6 h-6 animate-spin text-purple-400" /></div>;
  }

  return (
    <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-4">
      <div className="flex items-center gap-3 mb-4 pb-2 border-b border-slate-700/50">
        <Folder className="w-5 h-5 text-cyan-400" />
        <h3 className="font-bold text-white">Application Architecture</h3>
        {summary && (
          <div className="ml-auto flex gap-3 text-xs">
            <span className="text-gray-400">{summary.total_pages} pages</span>
            <span className="text-red-400">
              {pages.reduce((total, page) => total + (page.vulnerability_count || 0), 0)} vuln
            </span>
          </div>
        )}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {Object.keys(categoryNames).map((key) => {
          const catPages = byCategory[key] || [];
          const catInfo = categoryNames[key];
          return (
            <div key={key} className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/30 flex flex-col h-full">
              <div className="flex items-center gap-2 mb-3 text-cyan-300 border-b border-slate-700/30 pb-2">
                <span className="text-lg">{catInfo.icon}</span>
                <span className="font-semibold text-sm">{catInfo.name}</span>
                <span className="ml-auto text-xs text-gray-500 bg-slate-800 px-1.5 rounded">{catPages.length}</span>
              </div>
              <div className="space-y-2 overflow-y-auto custom-scrollbar flex-1 max-h-[200px]">
                {catPages.length === 0 ? (
                  <div className="text-xs text-gray-600 text-center py-2 italic">--</div>
                ) : (
                  catPages.map((page, idx) => (
                    <div key={idx} className={`p-2 rounded border ${getStatusColor(page)} transition-all hover:bg-slate-700/50 group relative`}>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(page)}
                        <span className="text-xs font-mono text-gray-300 truncate w-full" title={page.path}>{page.name}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const MissionIntelPanel = ({ seed }) => {
  return (
    <div className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 backdrop-blur-xl rounded-xl border border-purple-500/30 p-4 flex flex-col h-full" style={{ maxHeight: '450px', minHeight: '300px' }}>
      <div className="flex items-center gap-2 mb-3 pb-3 border-b border-purple-500/30 flex-shrink-0">
        <Terminal className="w-5 h-5 text-purple-400" />
        <h3 className="font-bold text-white">Mission Intel</h3>
      </div>
      <div className="space-y-3 text-sm overflow-y-auto custom-scrollbar">
        <div className="flex justify-between items-center p-3 bg-slate-900/50 rounded-lg border border-purple-500/20">
          <span className="text-gray-400">Mission Seed</span>
          <span className="font-mono text-purple-400 font-semibold">{seed || 'Random'}</span>
        </div>
        <div className="flex justify-between items-center p-3 bg-slate-900/50 rounded-lg border border-purple-500/20">
          <span className="text-gray-400">Target System</span>
          <a
            href="http://localhost:8080"
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-400 hover:text-cyan-300 font-mono flex items-center gap-1 transition-colors"
          >
            :8080
            <span className="text-xs">→</span>
          </a>
        </div>
        <div className="flex justify-between items-center p-3 bg-slate-900/50 rounded-lg border border-purple-500/20">
          <span className="text-gray-400">Status</span>
          <span className="text-green-400 flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            Active
          </span>
        </div>
        <div className="p-3 bg-slate-900/50 rounded-lg border border-purple-500/20 mt-4">
          <div className="text-xs text-gray-500 mb-2 uppercase tracking-wider font-bold">Objective</div>
          <p className="text-gray-300 leading-relaxed">
            Secure/Exploit the target infrastructure. Monitor logs for activity.
          </p>
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// EVASION LAB COMPONENT
// =============================================================================

const EvasionLabModal = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [payload, setPayload] = useState('<script>alert("XSS")</script>');
  const [encodedPayload, setEncodedPayload] = useState('');
  const [encodingSteps, setEncodingSteps] = useState([]);

  useEffect(() => {
    const handleOpen = () => setIsOpen(true);
    window.addEventListener('open-evasion-lab', handleOpen);
    return () => window.removeEventListener('open-evasion-lab', handleOpen);
  }, []);

  // eslint-disable-next-line no-unused-vars
  const handleDragEnd = (result) => {
    if (!result.destination) return;
    const items = Array.from(encodingSteps);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    setEncodingSteps(items);
    applyEncodings(payload, items);
  };

  const addStep = (type) => {
    const newSteps = [...encodingSteps, { id: `step-${Date.now()}`, type }];
    setEncodingSteps(newSteps);
    applyEncodings(payload, newSteps);
  };

  const removeStep = (index) => {
    const newSteps = encodingSteps.filter((_, i) => i !== index);
    setEncodingSteps(newSteps);
    applyEncodings(payload, newSteps);
  };

  const applyEncodings = (text, steps) => {
    let result = text;
    try {
      steps.forEach(step => {
        switch (step.type) {
          case 'base64':
            result = btoa(result);
            break;
          case 'url':
            result = encodeURIComponent(result);
            break;
          case 'hex':
            result = result.split('').map(c => '%' + c.charCodeAt(0).toString(16).padStart(2, '0')).join('');
            break;
          case 'unicode':
            result = result.split('').map(c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0')).join('');
            break;
          case 'html':
            result = result.split('').map(c => '&#' + c.charCodeAt(0) + ';').join('');
            break;
          case 'sql_char':
            result = 'CHAR(' + result.split('').map(c => c.charCodeAt(0)).join(',') + ')';
            break;
          default:
            break;
        }
      });
      setEncodedPayload(result);
    } catch (e) {
      setEncodedPayload('Error during encoding: ' + e.message);
    }
  };

  useEffect(() => {
    applyEncodings(payload, encodingSteps);
  }, [payload, encodingSteps]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[70] flex items-center justify-center p-6 animate-in fade-in duration-200">
      <div className="bg-slate-900 border-2 border-pink-500/50 rounded-2xl w-full max-w-5xl h-[85vh] flex flex-col shadow-2xl shadow-pink-500/20">
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-pink-600`}>
              <Folder className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Advanced Evasion Lab</h3>
              <p className="text-sm text-pink-300">WAF Bypass & Payload Crafting Studio</p>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-gray-400 hover:text-white"
          >
            <XCircle className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 overflow-hidden flex flex-col lg:flex-row">
          {/* Left Column: Input and Encoders */}
          <div className="w-full lg:w-1/2 border-r border-slate-700/50 p-6 flex flex-col overflow-y-auto custom-scrollbar">
            <h4 className="font-bold text-gray-300 mb-2 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-pink-400" />
              Raw Payload
            </h4>
            <textarea
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              className="w-full h-32 bg-black border border-slate-700 focus:border-pink-500 rounded-xl p-4 font-mono text-sm text-green-400 outline-none resize-none mb-6 shadow-inner"
              placeholder="Enter your raw payload..."
            />

            <h4 className="font-bold text-gray-300 mb-3 flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-400" />
              Available Encoders
            </h4>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-2 mb-6">
              {[
                { type: 'url', label: 'URL Encode', color: 'blue' },
                { type: 'base64', label: 'Base64', color: 'purple' },
                { type: 'hex', label: 'Hex Encoding', color: 'orange' },
                { type: 'unicode', label: 'Unicode', color: 'pink' },
                { type: 'html', label: 'HTML Entities', color: 'green' },
                { type: 'sql_char', label: 'SQL CHAR()', color: 'cyan' },
              ].map(enc => (
                <button
                  key={enc.type}
                  onClick={() => addStep(enc.type)}
                  className={`border border-${enc.color}-500/50 bg-${enc.color}-500/10 hover:bg-${enc.color}-500/20 text-${enc.color}-400 px-3 py-2 rounded-lg text-xs font-mono transition-all text-center flex items-center justify-center gap-1 group`}
                >
                  <span className="opacity-0 group-hover:opacity-100 transition-opacity w-0 group-hover:w-auto -ml-3 group-hover:mr-1">+</span>
                  {enc.label}
                </button>
              ))}
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 mt-auto">
              <h5 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Tips for WAF Bypass</h5>
              <ul className="text-xs text-gray-500 space-y-1 list-disc list-inside">
                <li>Double URL encoding can bypass poorly configured filters</li>
                <li>SQL Injection often bypasses filters using CHAR() concatenation</li>
                <li>Stack encoders logically (e.g., Hex -&gt; URL)</li>
              </ul>
            </div>
          </div>

          {/* Right Column: Encoding Chain and output */}
          <div className="w-full lg:w-1/2 bg-black/40 p-6 flex flex-col">
            <h4 className="font-bold text-gray-300 mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Encoding Chain Pipeline
            </h4>

            <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-4 min-h-[150px] mb-6 flex flex-col gap-2 relative">
              {encodingSteps.length === 0 ? (
                <div className="absolute inset-0 flex items-center justify-center text-gray-600 text-sm font-mono border-2 border-dashed border-slate-700 rounded-xl m-2">
                  Add encoders from the left panel to build your chain
                </div>
              ) : (
                encodingSteps.map((step, index) => (
                  <div key={step.id} className="flex items-center gap-2 bg-slate-800 p-2 rounded-lg border border-slate-600 group">
                    <div className="bg-slate-700 px-2 py-1 rounded text-xs text-gray-400 font-mono flex-shrink-0">
                      Step {index + 1}
                    </div>
                    <div className="font-mono text-sm text-white flex-1 relative overflow-hidden">
                      {step.type.toUpperCase()}
                      <div className="absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-slate-800 to-transparent pointer-events-none"></div>
                    </div>
                    <button
                      onClick={() => removeStep(index)}
                      className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity p-1"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>

            <h4 className="font-bold text-gray-300 mb-2 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-red-500" />
                Final Encoded Payload
              </div>

              <button
                onClick={() => {
                  navigator.clipboard.writeText(encodedPayload);
                }}
                className="text-xs bg-slate-800 hover:bg-slate-700 px-3 py-1 rounded border border-slate-600 text-gray-300 transition-colors"
              >
                Copy to Clipboard
              </button>
            </h4>
            <div className="flex-1 relative">
              <textarea
                value={encodedPayload}
                readOnly
                className="absolute inset-0 w-full h-full bg-[#0a0a0a] border border-slate-700 rounded-xl p-4 font-mono text-lg text-pink-400 outline-none resize-none shadow-inner"
              />
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// APP COMPONENT
// =============================================================================

const ToolOutputModal = ({ isOpen, onClose, toolName, output, loading }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] flex items-center justify-center p-6">
      <div className="bg-slate-900 border-2 border-slate-700 rounded-2xl w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-orange-600`}>
              <Terminal className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">{toolName} Output</h3>
              <p className="text-sm text-gray-400">Real-time security scan results</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-gray-400 hover:text-white"
          >
            <XCircle className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 p-6 overflow-hidden bg-black/40">
          {loading ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <Loader className="w-12 h-12 animate-spin text-orange-500 mb-4" />
              <h4 className="text-lg font-bold text-white italic">Scanning...</h4>
              <p className="text-gray-400 mt-2">This may take several minutes. Do not close this window.</p>
            </div>
          ) : (
            <pre className="h-full overflow-y-auto custom-scrollbar font-mono text-xs text-green-400 p-4 leading-relaxed whitespace-pre-wrap">
              {output || "No output captured."}
            </pre>
          )}
        </div>

        <div className="p-4 border-t border-slate-700 bg-slate-900/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded-xl text-white font-semibold transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// Defender View Component - Hunt for vulnerabilities
const DefenderView = ({ sessionId, vulnerabilities, defendedVulns, onUpdate }) => {
  const [challengeInfo, setChallengeInfo] = React.useState(null);
  const [pages, setPages] = React.useState([]);
  const [selectedPage, setSelectedPage] = React.useState(null);
  const [scanning, setScanning] = React.useState(false);
  const [discoveredVulns, setDiscoveredVulns] = React.useState([]);
  const [showCodeEditor, setShowCodeEditor] = React.useState(false);
  const [editingVuln, setEditingVuln] = React.useState(null);

  // Security Tool States
  const [toolModalOpen, setToolModalOpen] = React.useState(false);
  const [toolOutput, setToolOutput] = React.useState("");
  const [toolLoading, setToolLoading] = React.useState(false);
  const [activeTool, setActiveTool] = React.useState("");

  React.useEffect(() => {
    loadChallengeInfo();
    loadPages();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runZapScan = async () => {
    setToolModalOpen(true);
    setToolLoading(true);
    setActiveTool("OWASP ZAP");
    setToolOutput("Initializing ZAP Scanner...\nConnecting to ZAP API at localhost:8081...\nStarting spider and active scan on http://localhost:8080...");

    try {
      const response = await fetch(`${API_URL}/api/tools/zap/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_url: "http://localhost:8080" })
      });

      const data = await response.json();
      if (data.status === 'success') {
        const alerts = data.result.alerts || [];
        let report = `ZAP Scan Complete!\nFound ${alerts.length} potential vulnerabilities.\n\n`;

        alerts.forEach((alert, i) => {
          report += `[${i + 1}] ${alert.alert} (${alert.risk})\n`;
          report += `    URL: ${alert.url}\n`;
          report += `    Parameter: ${alert.param}\n`;
          report += `    Description: ${alert.description.substring(0, 200)}...\n\n`;
        });

        setToolOutput(report);
      } else {
        setToolOutput(`Error: ${data.message || 'Scan failed'}`);
      }
    } catch (err) {
      setToolOutput(`Error connecting to ZAP: ${err.message}`);
    }
    setToolLoading(false);
  };
  const loadChallengeInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/api/session/${sessionId}/challenge`);
      const data = await response.json();
      if (data.status === 'success') {
        setChallengeInfo(data);
      }
    } catch (err) {
      console.error('Failed to load challenge info:', err);
    }
  };
  const loadPages = async () => {
    try {
      const response = await fetch(`${API_URL}/api/session/${sessionId}/pages`);
      const data = await response.json();
      if (data.status === 'success') {
        setPages(data.pages);
      }
    } catch (err) {
      console.error('Failed to load pages:', err);
    }
  };
  const scanPage = async (page) => {
    setScanning(true);
    setSelectedPage(page);

    try {
      const response = await fetch(`${API_URL}/api/session/${sessionId}/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location: page })
      });

      const data = await response.json();

      if (data.found && data.vulnerabilities) {
        const newVulns = data.vulnerabilities.filter(
          v => !discoveredVulns.some(dv => dv.id === v.id)
        );
        setDiscoveredVulns([...discoveredVulns, ...newVulns]);
      }
    } catch (err) {
      console.error('Scan failed:', err);
    }

    setScanning(false);
  };
  return (
    <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
      <div className="flex items-center gap-3 mb-6">
        <Shield className="w-6 h-6 text-blue-400" />
        <h2 className="text-2xl font-bold font-display tracking-tight text-white">Defense Console</h2>

        <button
          onClick={runZapScan}
          disabled={toolLoading}
          className="ml-auto flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-500 hover:to-orange-400 text-white rounded-xl text-sm font-bold transition-all shadow-lg shadow-orange-500/20 active:scale-95 disabled:opacity-50"
        >
          {toolLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          Scan Entire Site (ZAP)
        </button>
      </div>

      <ToolOutputModal
        isOpen={toolModalOpen}
        onClose={() => setToolModalOpen(false)}
        toolName={activeTool}
        output={toolOutput}
        loading={toolLoading}
      />

      {/* Challenge Overview */}
      {challengeInfo && (
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-blue-400">Mission Briefing</h3>
          </div>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-slate-900/50 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">Total Threats</div>
              <div className="text-3xl font-bold text-blue-400">{challengeInfo.total_vulnerabilities}</div>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">Secured</div>
              <div className="text-3xl font-bold text-green-400">{challengeInfo.discovered_count}</div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-sm text-gray-300 font-semibold mb-2">Threat Severity Distribution:</div>
            {Object.entries(challengeInfo.severity_breakdown).map(([severity, count]) => (
              count > 0 && (
                <div key={severity} className="flex items-center gap-3">
                  <SeverityBadge severity={severity} />
                  <div className="flex-1 bg-slate-800/50 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${severity === 'critical' ? 'bg-red-500' :
                        severity === 'high' ? 'bg-orange-500' :
                          severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                        }`}
                      style={{ width: `${(count / challengeInfo.total_vulnerabilities) * 100}%` }}
                    />
                  </div>
                  <span className="text-gray-400 text-sm w-8">{count}</span>
                </div>
              )
            ))}
          </div>

          <div className="mt-4 p-3 bg-slate-900/50 rounded-lg">
            <p className="text-sm text-gray-300">{challengeInfo.hint}</p>
          </div>
        </div>
      )}
      {/* Application Pages to Scan */}
      <div className="mb-6">
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-cyan-400" />
          Scan Application Pages
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {pages.map(page => {
            const hasVulns = discoveredVulns.some(v => v.location === page.path);
            const isScanned = selectedPage === page.path;

            return (
              <button
                key={page.path}
                onClick={() => scanPage(page.path)}
                disabled={scanning}
                className={`relative p-4 rounded-xl text-left transition-all ${hasVulns
                  ? 'bg-red-900/30 border-2 border-red-500/50 shadow-lg shadow-red-500/20'
                  : isScanned
                    ? 'bg-green-900/30 border-2 border-green-500/50'
                    : 'bg-slate-800/50 border-2 border-slate-700/30 hover:border-slate-600/50'
                  }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-sm text-cyan-400">{page.name}</span>
                  {hasVulns && <AlertTriangle className="w-4 h-4 text-red-400" />}
                  {isScanned && !hasVulns && <CheckCircle className="w-4 h-4 text-green-400" />}
                </div>
                <div className="text-xs text-gray-400">
                  {scanning && selectedPage === page ? 'Scanning...' : 'Click to scan'}
                </div>
                {hasVulns && (
                  <div className="mt-2">
                    <span className="text-xs bg-red-500/20 text-red-300 px-2 py-1 rounded">
                      {discoveredVulns.filter(v => v.location === page.path).length} vulnerability found
                    </span>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
      {/* Discovered Vulnerabilities */}
      {discoveredVulns.length > 0 && (
        <div>
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5 text-orange-400" />
            Discovered Vulnerabilities ({discoveredVulns.length})
          </h3>
          <div className="space-y-4">
            {discoveredVulns.map(vuln => {
              const isDefended = defendedVulns.includes(vuln.id);

              return (
                <div
                  key={vuln.id}
                  className={`rounded-xl p-5 border-2 transition-all ${isDefended
                    ? 'bg-green-900/30 border-green-500/50 shadow-lg shadow-green-500/20'
                    : 'bg-slate-800/50 border-red-500/30'
                    }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-mono text-sm text-cyan-400 bg-slate-900/50 px-3 py-1 rounded-lg">
                          {vuln.id}
                        </span>
                        <SeverityBadge severity={vuln.severity} />
                      </div>
                      <p className="text-sm text-gray-300 mb-2">{vuln.description}</p>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-gray-400 bg-slate-900/50 px-2 py-1 rounded">
                          {vuln.location}
                        </span>
                        {vuln.hint && (
                          <span className="text-orange-400 bg-orange-900/30 px-2 py-1 rounded">
                            {vuln.hint}
                          </span>
                        )}
                      </div>
                    </div>
                    {isDefended && (
                      <div className="flex items-center gap-2 text-green-400 text-xs bg-green-900/30 px-3 py-1 rounded-lg">
                        <CheckCircle className="w-4 h-4" />
                        Secured
                      </div>
                    )}
                  </div>
                  {!isDefended && (
                    <div className="flex gap-3 mt-4">
                      <button
                        onClick={() => {
                          setEditingVuln(vuln);
                          setShowCodeEditor(true);
                        }}
                        className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 px-4 py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-all transform hover:scale-105 shadow-lg shadow-blue-500/30"
                      >
                        <Terminal className="w-4 h-4" />
                        Fix Vulnerability
                      </button>

                      <a
                        href={`http://localhost:8080${vuln.location}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-5 py-3 bg-slate-700/50 hover:bg-slate-600/50 rounded-xl text-sm font-medium transition-all flex items-center gap-2"
                      >
                        Test Live
                        <span className="text-cyan-400">→</span>
                      </a>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
      {/* Code Editor Modal */}
      {showCodeEditor && editingVuln && (
        <CodeEditorModal
          vuln={editingVuln}
          sessionId={sessionId}
          role="defender"
          onClose={() => {
            setShowCodeEditor(false);
            setEditingVuln(null);
          }}
          onUpdate={() => {
            loadChallengeInfo();
            onUpdate();
          }}
        />
      )}
    </div>
  );
};

// Attacker View Component - Interactive exploitation
const AttackerView = ({ sessionId, vulnerabilities, exploitedVulns, onUpdate }) => {
  const [selectedPage, setSelectedPage] = React.useState(null);
  const [attackType, setAttackType] = React.useState('');
  const [payload, setPayload] = React.useState('');
  const [attacking, setAttacking] = React.useState(false);
  const [attackResult, setAttackResult] = React.useState(null);
  const [pages, setPages] = React.useState([]);

  // Security Tool States
  const [viewMode, setViewMode] = React.useState('manual'); // 'manual' or 'tools'
  const [toolModalOpen, setToolModalOpen] = React.useState(false);
  const [toolOutput, setToolOutput] = React.useState("");
  const [toolLoading, setToolLoading] = React.useState(false);
  const [activeTool, setActiveTool] = React.useState("");

  React.useEffect(() => {
    loadPages();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runSqlmap = async () => {
    if (!selectedPage) return;
    setToolModalOpen(true);
    setToolLoading(true);
    setActiveTool("sqlmap");
    setToolOutput(`Starting SQL Injection scan on ${selectedPage}...\nAutomatically logging in and testing parameters...\nThis may take 10-30 seconds.`);

    try {
      const response = await fetch(`${API_URL}/api/tools/sqlmap/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_url: `http://localhost:8080${selectedPage}`,
          session_id: sessionId
        })
      });

      const data = await response.json();
      if (data.status === 'success') {
        const result = data.result;
        let output = result.output || '';
        if (result.found) {
          output = `SQL INJECTION DETECTED!\n\n${output}`;
        } else {
          output = `No SQL injection found on this page. This could mean:\n` +
            `  • The vulnerability has been patched\n` +
            `  • The parameter is not vulnerable on this page\n` +
            `  • Try another page from the list\n\n${output}`;
        }
        setToolOutput(output);
      } else {
        setToolOutput(`Error: ${data.message || 'Scan failed'}`);
      }
    } catch (err) {
      setToolOutput(`Error: ${err.message}`);
    }
    setToolLoading(false);
  };

  const runXssScanner = async () => {
    if (!selectedPage) return;
    setToolModalOpen(true);
    setToolLoading(true);
    setActiveTool("XSS Scanner");
    setToolOutput(`🔍 Starting XSS scan on ${selectedPage}...\nInjecting payloads and checking for reflection...\nThis may take 10-30 seconds.`);

    try {
      const response = await fetch(`${API_URL}/api/tools/xss/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_url: `http://localhost:8080${selectedPage}`,
          session_id: sessionId
        })
      });

      const data = await response.json();
      if (data.status === 'success') {
        const result = data.result;
        let output = result.output || '';
        if (result.found) {
          output = `CROSS-SITE SCRIPTING (XSS) DETECTED!\n\n${output}`;
        } else {
          output = `No XSS found on this page. This could mean:\n` +
            `  • The vulnerability has been patched (output is HTML-escaped)\n` +
            `  • The parameter is not reflected on this page\n` +
            `  • Try another page from the list\n\n${output}`;
        }
        setToolOutput(output);
      } else {
        setToolOutput(`Error: ${data.message || 'Scan failed'}`);
      }
    } catch (err) {
      setToolOutput(`Error: ${err.message}`);
    }
    setToolLoading(false);
  };

  const loadPages = async () => {
    try {
      const response = await fetch(`${API_URL}/api/session/${sessionId}/pages`);
      const data = await response.json();
      if (data.status === 'success') {
        setPages(data.pages);
      }
    } catch (err) {
      console.error('Failed to load pages:', err);
    }
  };
  const attackTypes = [
    { value: 'sqli', label: 'SQL Injection', icon: 'Injection' },
    { value: 'xss', label: 'Cross-Site Scripting', icon: 'Link' },
    { value: 'lfi', label: 'Local File Inclusion', icon: 'Folder' },
    { value: 'rce', label: 'Remote Code Execution', icon: 'Lightning' },
    { value: 'csrf', label: 'CSRF', icon: 'Fishing' },
    { value: 'xxe', label: 'XXE Injection', icon: 'Document' },
    { value: 'ssrf', label: 'SSRF', icon: 'Globe' },
    { value: 'idor', label: 'IDOR', icon: 'Unlock' },
  ];
  const payloadHints = {
    sqli: ["' OR '1'='1", "' UNION SELECT null--", "admin'--", "1' AND 1=1--"],
    // eslint-disable-next-line no-script-url
    xss: ["<script>alert('XSS')</script>", "<img src=x onerror=alert(1)>", "java_script:alert(1)", "<svg/onload=alert(1)>"],
    lfi: ["../../../../etc/passwd", "../../../config/database.php", "php://filter/read=convert.base64-encode/resource=index.php"],
    rce: ["; ls -la", "| whoami", "&& cat /etc/passwd", "`id`"],
    xxe: ["<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><foo>&xxe;</foo>"],
    ssrf: ["http://127.0.0.1:8080", "http://localhost/admin", "file:///etc/passwd"],
    csrf: ["<form action='http://localhost:8080/settings.php' method='POST'>"],
    idor: ["id=1", "user_id=999", "../admin/data"]
  };
  const launchAttack = async () => {
    if (!selectedPage || !attackType || !payload.trim()) {
      setAttackResult({ success: false, message: 'Please select page, attack type, and enter payload' });
      return;
    }
    setAttacking(true);
    setAttackResult(null);
    try {
      const response = await fetch(`${API_URL}/api/attacker/test/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          page: selectedPage,
          attack_type: attackType,
          payload: payload
        })
      });
      const data = await response.json();
      setAttackResult(data);

      if (data.success && data.points_awarded > 0) {
        onUpdate();
      }
    } catch (err) {
      setAttackResult({ success: false, message: 'Attack failed: ' + err.message });
    }
    setAttacking(false);
  };
  return (
    <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
      <div className="flex items-center gap-3 mb-6">
        <Sword className="w-6 h-6 text-red-400" />
        <h2 className="text-2xl font-bold font-display tracking-tight text-white">Attack Console</h2>

        <div className="ml-auto flex bg-slate-800/50 p-1 rounded-xl border border-slate-700/50">
          <button
            onClick={() => setViewMode('manual')}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${viewMode === 'manual'
              ? 'bg-red-600 text-white shadow-lg shadow-red-500/20'
              : 'text-gray-400 hover:text-gray-200'
              }`}
          >
            Manual
          </button>
          <button
            onClick={() => setViewMode('tools')}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${viewMode === 'tools'
              ? 'bg-orange-600 text-white shadow-lg shadow-orange-500/20'
              : 'text-gray-400 hover:text-gray-200'
              }`}
          >
            Tools
          </button>
        </div>
      </div>

      <ToolOutputModal
        isOpen={toolModalOpen}
        onClose={() => setToolModalOpen(false)}
        toolName={activeTool}
        output={toolOutput}
        loading={toolLoading}
      />
      {/* Target Selection */}
      <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-6 mb-6">
        <h3 className="text-xl font-bold text-red-400 mb-4">Target Selection</h3>

        <div className="grid grid-cols-2 gap-3 mb-4">
          {pages.map(page => (
            <button
              key={page.path}
              onClick={() => setSelectedPage(page.path)}
              className={`p-3 rounded-lg text-left transition-all ${selectedPage === page.path
                ? 'bg-red-600 border-2 border-red-400'
                : 'bg-slate-800/50 border-2 border-slate-700/30 hover:border-red-500/50'
                }`}
            >
              <div className="font-mono text-sm text-cyan-400">{page.name}</div>
            </button>
          ))}
        </div>
        {selectedPage && (
          <a
            href={`http://localhost:8080${selectedPage}`}
            target="_blank"
            rel="noopener noreferrer"
            className="block w-full bg-slate-800/50 hover:bg-slate-700/50 px-4 py-3 rounded-lg text-center text-sm font-medium transition-all"
          >
            Open Target Page in Browser
            <span className="ml-2 text-cyan-400">→</span>
          </a>
        )}
      </div>
      {/* Attack Configuration Selection */}
      {selectedPage && viewMode === 'manual' && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div>
            <label className="block text-sm font-semibold mb-3 text-gray-300">
              Attack Vector
            </label>
            <div className="grid grid-cols-2 gap-3">
              {attackTypes.map(type => (
                <button
                  key={type.value}
                  onClick={() => {
                    setAttackType(type.value);
                    setPayload('');
                  }}
                  className={`p-4 rounded-xl text-left transition-all ${attackType === type.value
                    ? 'bg-gradient-to-r from-red-600 to-red-700 border-2 border-red-400'
                    : 'bg-slate-800/50 border-2 border-slate-700/30 hover:border-red-500/50'
                    }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xl">{type.icon}</span>
                    <span className="font-semibold text-sm">{type.label}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
          {attackType && (
            <>
              {/* Payload Input */}
              <div>
                <label className="block text-sm font-semibold mb-3 text-gray-300">
                  Craft Payload
                </label>
                <textarea
                  value={payload}
                  onChange={(e) => setPayload(e.target.value)}
                  placeholder={`Enter your ${attackTypes.find(t => t.value === attackType)?.label} payload...`}
                  className="w-full bg-slate-950 border-2 border-slate-700 focus:border-red-500 rounded-xl px-4 py-3 text-sm text-gray-200 outline-none transition-all resize-none font-mono"
                  rows={6}
                />

                {/* Payload Hints */}
                <div className="mt-3">
                  <p className="text-xs text-gray-400 mb-2">Payload Examples:</p>
                  <div className="flex flex-wrap gap-2">
                    {(payloadHints[attackType] || []).map((hint, idx) => (
                      <button
                        key={idx}
                        onClick={() => setPayload(hint)}
                        className="text-xs bg-slate-800/50 hover:bg-slate-700/50 px-3 py-1.5 rounded-lg text-gray-300 hover:text-white transition-colors font-mono"
                      >
                        {hint}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              {/* Attack Button */}
              <button
                onClick={launchAttack}
                disabled={attacking || !payload.trim()}
                className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 disabled:opacity-50 disabled:cursor-not-allowed px-6 py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all transform hover:scale-105 disabled:scale-100 shadow-lg shadow-red-500/30"
              >
                {attacking ? (
                  <>
                    <Loader className="w-6 h-6 animate-spin" />
                    Executing Attack...
                  </>
                ) : (
                  <>
                    <Zap className="w-6 h-6" />
                    Launch Attack
                  </>
                )}
              </button>
              {/* Attack Result */}
              {attackResult && (
                <div className={`p-6 rounded-xl border-2 ${attackResult.success
                  ? 'bg-green-500/10 border-green-500/50'
                  : 'bg-red-500/10 border-red-500/50'
                  } animate-slideIn`}>
                  <div className="flex items-start gap-4">
                    {attackResult.success ? (
                      <CheckCircle className="w-8 h-8 text-green-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-8 h-8 text-red-400 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <h4 className={`font-bold text-lg mb-2 ${attackResult.success ? 'text-green-400' : 'text-red-400'
                        }`}>
                        {attackResult.success ? 'Exploit Successful!' : 'Attack Failed'}
                      </h4>
                      <p className="text-gray-300 mb-3">{attackResult.message}</p>

                      {attackResult.success && attackResult.vulnerability && (
                        <div className="bg-slate-900/50 rounded-lg p-4 mb-3">
                          <div className="text-sm space-y-2">
                            <div className="flex items-center gap-2">
                              <span className="text-gray-400">Vulnerability:</span>
                              <span className="font-mono text-cyan-400">{attackResult.vulnerability.id}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-400">Severity:</span>
                              <SeverityBadge severity={attackResult.vulnerability.severity} />
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-400">Description:</span>
                              <span className="text-gray-300">{attackResult.vulnerability.description}</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {attackResult.points_awarded > 0 && (
                        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                          <p className="text-yellow-300 font-semibold flex items-center gap-2">
                            <Trophy className="w-5 h-5" />
                            +{attackResult.points_awarded} points earned!
                          </p>
                        </div>
                      )}
                      {attackResult.defended && (
                        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 mt-3">
                          <p className="text-blue-300 text-sm flex items-center gap-2">
                            <Shield className="w-4 h-4" />
                            This vulnerability has been patched by the defender
                          </p>
                        </div>
                      )}
                      {!attackResult.success && attackResult.hint && (
                        <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-3 mt-3">
                          <p className="text-orange-300 text-sm">
                            Hint: {attackResult.hint}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Automated Tools Configuration */}
      {selectedPage && viewMode === 'tools' && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div>
            <label className="block text-sm font-semibold mb-3 text-gray-300">
              Select Automated Tool
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={runSqlmap}
                disabled={toolLoading}
                className="p-5 rounded-xl border-2 border-orange-500/30 bg-orange-500/10 hover:bg-orange-500/20 transition-all text-left group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-orange-600 group-hover:scale-110 transition-transform">
                    <Terminal className="w-5 h-5 text-white" />
                  </div>
                  <span className="font-bold text-white text-lg">sqlmap</span>
                </div>
                <p className="text-xs text-gray-400">Automated SQL Injection and database takeover tool.</p>
                <div className="mt-4 flex items-center gap-2 text-orange-400 text-xs font-bold">
                  {toolLoading && activeTool === "sqlmap" ? <Loader className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                  LAUNCH SCAN
                </div>
              </button>

              <button
                onClick={runXssScanner}
                disabled={toolLoading}
                className="p-5 rounded-xl border-2 border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 transition-all text-left group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-purple-600 group-hover:scale-110 transition-transform">
                    <Zap className="w-5 h-5 text-white" />
                  </div>
                  <span className="font-bold text-white text-lg">XSS Scanner</span>
                </div>
                <p className="text-xs text-gray-400">Automatic XSS vulnerability detector and exploiter.</p>
                <div className="mt-4 flex items-center gap-2 text-purple-400 text-xs font-bold">
                  {toolLoading && activeTool === "XSS Scanner" ? <Loader className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                  LAUNCH SCAN
                </div>
              </button>

              <div className="flex items-center gap-3 mb-1">
                <div className="flex items-center gap-3 mb-1">
        <h3 className="text-xl font-bold text-white">Attacking Scenarios</h3>
        <span className="px-2 py-0.5 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-[10px] font-bold text-white uppercase tracking-wider shadow-lg shadow-purple-500/30 animate-pulse">
          Coming Soon
        </span>
      </div>
                <span className="px-2 py-0.5 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-[10px] font-bold text-white uppercase tracking-wider shadow-lg shadow-purple-500/30 animate-pulse">
                  Coming Soon
                </span>
              </div>

              <button
                onClick={async () => {
                  if (!selectedPage) return;
                  setToolModalOpen(true);
                  setToolLoading(true);
                  setActiveTool("Page Hint");
                  setToolOutput(`🔍 Analyzing ${selectedPage} for potential attack vectors...\nContacting HackOps Oracle...`);
                  try {
                    const response = await fetch(`${API_URL}/api/tools/page-hint/${sessionId}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ target_url: `http://localhost:8080${selectedPage}` })
                    });
                    const data = await response.json();
                    if (data.status === 'success') {
                      setToolOutput(`Oracle Hint for ${selectedPage}:\n\n` +
                        `Message: ${data.hint.message}\n` +
                        (data.hint.vulnerable_params?.length ? `Vulnerable Params: ${data.hint.vulnerable_params.join(', ')}\n` : '') +
                        `Advice: ${data.hint.advice}`
                      );
                    } else {
                      setToolOutput(`Error: ${data.message}`);
                    }
                  } catch (err) {
                    setToolOutput(`Error: ${err.message}`);
                  }
                  setToolLoading(false);
                }}
                disabled={toolLoading}
                className="p-5 rounded-xl border-2 border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 transition-all text-left group gap-2 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg bg-cyan-600 group-hover:scale-110 transition-transform">
                      <Terminal className="w-5 h-5 text-white" />
                    </div>
                    <span className="font-bold text-white text-lg">Page Hint Oracle</span>
                  </div>
                  <p className="text-xs text-gray-400">Get an AI-assisted hint about what parameters to test.</p>
                </div>
                <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold">
                  {toolLoading && activeTool === "Page Hint" ? <Loader className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                  GET HINT
                </div>
              </button>

              <button
                onClick={() => {
                  window.dispatchEvent(new CustomEvent('open-evasion-lab'));
                }}
                className="p-5 rounded-xl border-2 border-pink-500/30 bg-pink-500/10 hover:bg-pink-500/20 transition-all text-left group gap-2 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg bg-pink-600 group-hover:scale-110 transition-transform">
                      <Folder className="w-5 h-5 text-white" />
                    </div>
                    <span className="font-bold text-white text-lg">Evasion Lab</span>
                  </div>
                  <p className="text-xs text-gray-400">Craft and encode complex payloads to bypass WAF.</p>
                </div>
                <div className="flex items-center gap-2 text-pink-400 text-xs font-bold">
                  <Play className="w-3 h-3" />
                  OPEN LAB
                </div>
              </button>

            </div>
          </div>

          <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-4">
            <h4 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Tool Tips</h4>
            <ul className="text-xs text-gray-400 space-y-2 list-disc list-inside">
              <li>Use <b>sqlmap</b> for pages with search fields or URL parameters (e.g., Search, Product Details).</li>
              <li>Use <b>XSS Scanner</b> for pages that reflect user input back (e.g., Search, Reviews).</li>
              <li>Scans complete in 10-30 seconds. Results show which parameter is vulnerable.</li>
            </ul>
          </div>
        </div>
      )}

      {/* Exploitation Progress */}
      <div className="mt-6 bg-slate-800/30 rounded-xl p-5 border border-slate-700/30">
        <h4 className="font-semibold text-sm text-gray-400 mb-3">EXPLOITATION PROGRESS</h4>
        <div className="space-y-2">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-400">Compromised Targets</span>
            <span className="text-red-400 font-bold">{exploitedVulns.length} / {vulnerabilities.length}</span>
          </div>
          <div className="w-full bg-slate-900/50 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-red-600 to-red-700 h-3 rounded-full transition-all duration-500"
              style={{ width: `${(exploitedVulns.length / Math.max(vulnerabilities.length, 1)) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Code Editor Modal Component
const CodeEditorModal = ({ vuln, sessionId, role, onClose, onUpdate }) => {
  const [code, setCode] = React.useState('');
  const [originalCode, setOriginalCode] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [successMessage, setSuccessMessage] = React.useState(null);
  const [testPayload, setTestPayload] = React.useState('');
  const [testResult, setTestResult] = React.useState(null);
  const [semgrepResults, setSemgrepResults] = React.useState(null);


  React.useEffect(() => {
    loadCode();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vuln.id]);

  const loadCode = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/code/view/${sessionId}/${vuln.id}`);
      const data = await response.json();

      if (data.status === 'success') {
        setCode(data.source_code);
        setOriginalCode(data.source_code);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Failed to load code: ' + err.message);
    }
    setLoading(false);
  };

  const handleSaveCode = async () => {
    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await fetch(`${API_URL}/api/code/update/${sessionId}/${vuln.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
      });

      const data = await response.json();

      if (data.status === 'success') {
        let successMsg = `Code saved! ${data.points_awarded > 0 ? `+${data.points_awarded} points` : ''}`;
        setSuccessMessage(successMsg);

        // Check for Semgrep results in the message
        if (data.message && data.message.includes('[SAST Warning')) {
          setSemgrepResults(data.message.split('[SAST Warning:')[1].split(']')[0]);
        }

        try {
          if (onUpdate) onUpdate();
        } catch (updateErr) {
          console.error("Post-save update failed:", updateErr);
        }

        // Auto-close after 2 seconds
        setTimeout(() => {
          onClose();
        }, 2000);
      } else {
        setError(data.message || 'Failed to save code');
      }
    } catch (err) {
      setError('Failed to save code: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleTestExploit = async () => {
    if (!testPayload.trim()) {
      setError('Please enter a payload to test');
      return;
    }

    setLoading(true);
    setError(null);
    setTestResult(null);

    try {
      const response = await fetch(`${API_URL}/api/code/test/${sessionId}/${vuln.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload: testPayload })
      });

      const data = await response.json();

      if (data.status === 'success') {
        setTestResult(data);
        if (data.points_awarded > 0 && onUpdate) {
          onUpdate();
        }
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Failed to test exploit: ' + err.message);
    }
    setLoading(false);
  };

  const handleResetCode = () => {
    setCode(originalCode);
    setSuccessMessage(null);
    setError(null);
  };

  const getExploitHints = () => {
    const hints = {
      sqli: ["Try: ' OR '1'='1", "' UNION SELECT null--", "admin'--"],
      xss: ["<script>alert('XSS')</script>", "<img src=x onerror=alert(1)>", "java_script:alert(1)"],
      lfi: ["../../../../etc/passwd", "../../../config/database.php", "php://filter/read=convert.base64-encode/resource=index.php"],
      rce: ["; ls -la", "| whoami", "&& cat /etc/passwd"],
      xxe: ["<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><foo>&xxe;</foo>"],
      ssrf: ["http://127.0.0.1:8080", "http://localhost/admin", "file:///etc/passwd"],
      csrf: ["<form action='http://localhost:8080/change_password.php' method='POST'>"],
      idor: ["id=1", "user_id=999", "../admin/data"]
    };
    return hints[vuln.type] || ["Try different payloads"];
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
      <div className="bg-slate-900 rounded-3xl border-2 border-slate-700 max-w-6xl w-full max-h-[90vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-6 border-b border-slate-700">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Terminal className={`w-6 h-6 ${role === 'attacker' ? 'text-red-400' : 'text-blue-400'}`} />
                <h2 className="text-2xl font-bold text-white">
                  {role === 'attacker' ? 'Exploit Analysis' : 'Code Defense'}
                </h2>
              </div>
              <div className="flex items-center gap-3 flex-wrap">
                <span className="font-mono text-sm text-cyan-400 bg-slate-800/50 px-3 py-1 rounded-lg">
                  {vuln.id}
                </span>
                <SeverityBadge severity={vuln.severity} />
                <span className="text-sm text-gray-400">{vuln.location}</span>
              </div>
              <p className="text-gray-300 mt-2">{vuln.description}</p>
            </div>
            <button
              onClick={onClose}
              className="ml-4 w-10 h-10 rounded-xl bg-slate-800/50 hover:bg-slate-700/50 flex items-center justify-center transition-colors text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-200px)] custom-scrollbar">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader className="w-12 h-12 animate-spin text-purple-500" />
            </div>
          ) : (
            <div className="p-6 space-y-6">
              {/* Messages */}
              {error && (
                <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 flex items-center gap-3 animate-slideIn">
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                  <span className="text-sm text-red-300">{error}</span>
                </div>
              )}

              {successMessage && (
                <div className="bg-green-500/10 border border-green-500/50 rounded-xl p-4 flex flex-col gap-2 animate-slideIn">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                    <span className="text-sm text-green-300 font-bold">{successMessage}</span>
                  </div>
                  {semgrepResults && (
                    <div className="mt-2 p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                      <p className="text-xs text-orange-400 font-bold flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        SAST RECOMMENDATION:
                      </p>
                      <p className="text-xs text-orange-300 mt-1">{semgrepResults}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Code Editor */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <label className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
                    {role === 'attacker' ? 'Vulnerable Source Code (Read-Only)' : 'Source Code Editor'}
                  </label>
                  {role === 'defender' && (
                    <button
                      onClick={handleResetCode}
                      className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Reset to Original
                    </button>
                  )}
                </div>
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  readOnly={role === 'attacker'}
                  className={`w-full bg-slate-950 border-2 ${role === 'attacker' ? 'border-slate-700 cursor-not-allowed' : 'border-slate-600 focus:border-blue-500'
                    } rounded-xl px-4 py-3 font-mono text-sm text-gray-200 outline-none transition-all resize-none`}
                  style={{ minHeight: '400px' }}
                  spellCheck={false}
                />
              </div>

              {/* Attacker: Exploit Tester */}
              {role === 'attacker' && (
                <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-6">
                  <h3 className="text-lg font-bold text-red-400 mb-4 flex items-center gap-2">
                    <Zap className="w-5 h-5" />
                    Exploit Payload Tester
                  </h3>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Craft Your Payload
                      </label>
                      <textarea
                        value={testPayload}
                        onChange={(e) => setTestPayload(e.target.value)}
                        placeholder="Enter your exploit payload here..."
                        className="w-full bg-slate-950 border-2 border-slate-700 focus:border-red-500 rounded-xl px-4 py-3 text-sm text-gray-200 outline-none transition-all resize-none"
                        rows={4}
                      />
                    </div>

                    <div>
                      <p className="text-xs text-gray-400 mb-2">Payload Hints:</p>
                      <div className="flex flex-wrap gap-2">
                        {getExploitHints().map((hint, idx) => (
                          <button
                            key={idx}
                            onClick={() => setTestPayload(hint)}
                            className="text-xs bg-slate-800/50 hover:bg-slate-700/50 px-3 py-1.5 rounded-lg text-gray-300 hover:text-white transition-colors font-mono"
                          >
                            {hint}
                          </button>
                        ))}
                      </div>
                    </div>

                    <button
                      onClick={handleTestExploit}
                      disabled={loading || !testPayload.trim()}
                      className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 disabled:opacity-50 disabled:cursor-not-allowed px-6 py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all transform hover:scale-105 disabled:scale-100 shadow-lg shadow-red-500/30"
                    >
                      <Zap className="w-5 h-5" />
                      Test Exploit
                    </button>

                    {testResult && (
                      <div className={`p-4 rounded-xl border-2 ${testResult.success
                        ? 'bg-green-500/10 border-green-500/50'
                        : 'bg-red-500/10 border-red-500/50'
                        }`}>
                        <div className="flex items-start gap-3">
                          {testResult.success ? (
                            <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0" />
                          ) : (
                            <XCircle className="w-6 h-6 text-red-400 flex-shrink-0" />
                          )}
                          <div>
                            <p className={`font-semibold ${testResult.success ? 'text-green-400' : 'text-red-400'}`}>
                              {testResult.message}
                            </p>
                            {testResult.points_awarded > 0 && (
                              <p className="text-sm text-green-300 mt-1">
                                {testResult.points_awarded} points earned!
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Defender: Save Button */}
              {role === 'defender' && (
                <div className="flex gap-4">
                  <button
                    onClick={handleSaveCode}
                    disabled={saving || code === originalCode}
                    className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed px-6 py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all transform hover:scale-105 disabled:scale-100 shadow-lg shadow-blue-500/30"
                  >
                    {saving ? (
                      <>
                        <Loader className="w-6 h-6 animate-spin" />
                        Applying Patch...
                      </>
                    ) : (
                      <>
                        <Shield className="w-6 h-6" />
                        Deploy Patch
                      </>
                    )}
                  </button>
                  <a
                    href={`http://localhost:8080${vuln.location}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-6 py-4 bg-slate-700/50 hover:bg-slate-600/50 rounded-xl font-semibold flex items-center gap-2 transition-all"
                  >
                    Test Live
                    <span className="text-cyan-400">→</span>
                  </a>
                </div>
              )}

              {/* Attacker: View Live Button */}
              {role === 'attacker' && (
                <a
                  href={`http://localhost:8080${vuln.location}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full bg-slate-700/50 hover:bg-slate-600/50 px-6 py-4 rounded-xl font-semibold text-center transition-all"
                >
                  🌐 Open Target in Browser
                  <span className="ml-2 text-cyan-400">→</span>
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// API Service
const api = {
  async startEnvironment(seed = null, difficulty = 'easy', role = 'red') {
    const res = await fetch(`${API_URL}/api/environment/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seed, difficulty, role })
    });
    return res.json();
  },
  async stopEnvironment() {
    const res = await fetch(`${API_URL}/api/environment/stop`, { method: 'POST' });
    return res.json();
  },
  async getEnvironmentStatus() {
    const res = await fetch(`${API_URL}/api/environment/status`);
    return res.json();
  },
  async getSession(sessionId) {
    const res = await fetch(`${API_URL}/api/session/${sessionId}`);
    return res.json();
  },
  async getVulnerabilities(sessionId) {
    const res = await fetch(`${API_URL}/api/session/${sessionId}/vulnerabilities`);
    return res.json();
  },
  async reportExploit(sessionId, vulnId, details) {
    const res = await fetch(`${API_URL}/api/exploit/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, vuln_id: vulnId, details })
    });
    return res.json();
  },
  async applyDefense(sessionId, vulnId, fixCommand) {
    const res = await fetch(`${API_URL}/api/defense/apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, vuln_id: vulnId, fix_command: fixCommand })
    });
    return res.json();
  },
  async getLogs() {
    const res = await fetch(`${API_URL}/api/logs`);
    return res.json();
  }
};

// =============================================================================
// SEMGREP MODAL COMPONENT (Custom File Scanning)
// =============================================================================
const SemgrepModal = ({ isOpen, onClose, sessionId, onScan }) => {
  const [pages, setPages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && sessionId) {
      fetchPages();
    } else {
      setInputValue('');
      setSuggestions([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, sessionId]);

  const fetchPages = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/session/${sessionId}/pages`);
      const data = await response.json();
      if (data.status === 'success') {
        // Strip leading slash for easier typing
        setPages(data.pages.map(p => p.path.startsWith('/') ? p.path.substring(1) : p.path));
      }
    } catch (err) {
      console.error('Failed to load pages for Semgrep modal:', err);
    }
    setLoading(false);
  };

  const calculateSimilarity = (a, b) => {
    // Simple similarity based on how many characters match
    const str1 = a.toLowerCase();
    const str2 = b.toLowerCase();
    let matches = 0;
    for (let i = 0; i < Math.min(str1.length, str2.length); i++) {
      if (str1[i] === str2[i]) matches++;
    }
    return matches;
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);

    if (!value.trim()) {
      setSuggestions([]);
      return;
    }

    const valLower = value.toLowerCase();

    // First try finding exact prefix matches
    let matches = pages.filter(p => p.toLowerCase().startsWith(valLower));

    // If no exact prefixes, fallback to substring/similarity
    if (matches.length === 0) {
      matches = [...pages].sort((a, b) => {
        // Sort by similarity score descending
        const scoreA = calculateSimilarity(a, valLower) + (a.toLowerCase().includes(valLower) ? 5 : 0);
        const scoreB = calculateSimilarity(b, valLower) + (b.toLowerCase().includes(valLower) ? 5 : 0);
        return scoreB - scoreA;
      }).slice(0, 5); // Take top 5
    }

    setSuggestions(matches);
  };

  const handleSelect = (page) => {
    setInputValue(page);
    setSuggestions([]);
  };

  const handleScanClick = () => {
    if (!inputValue.trim()) return;
    onScan(inputValue);
    onClose();
  };

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
        <div className="p-5 border-b border-slate-800 flex justify-between items-center">
          <h3 className="font-bold text-white flex items-center gap-2">
            <Search className="w-5 h-5 text-purple-400" />
            Semgrep SAST Scanner
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">✕</button>
        </div>
        <div className="p-6">
          <label className="block text-sm font-semibold text-gray-300 mb-2">Target File</label>
          <p className="text-xs text-gray-400 mb-4">
            Type the name of the file you want to analyze (e.g., <code>search.php</code>).
          </p>

          <div className="relative">
            <input
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              className="w-full bg-slate-950 border border-slate-700 focus:border-purple-500 rounded-xl px-4 py-3 text-sm text-white outline-none transition-all placeholder:text-slate-600"
              placeholder="Start typing..."
              autoFocus
            />

            {loading ? (
              <div className="absolute right-3 top-3"><Loader className="w-5 h-5 animate-spin text-purple-500" /></div>
            ) : suggestions.length > 0 ? (
              <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-slate-700 rounded-xl overflow-hidden z-20 shadow-xl max-h-48 overflow-y-auto">
                {suggestions.map(s => (
                  <button
                    key={s}
                    className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-slate-700 hover:text-white transition-colors border-b border-slate-700/50 last:border-0"
                    onClick={() => handleSelect(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <button
            onClick={handleScanClick}
            disabled={!inputValue.trim()}
            className="mt-6 w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-purple-500/20 text-white"
          >
            <Shield className="w-5 h-5" />
            Launch Diagnostics
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};

// =============================================================================
// TOOLS PANEL COMPONENT
// =============================================================================

const ToolsPanel = ({ sessionId, role, difficulty, vulnerabilities }) => {
  const [tools, setTools] = React.useState({ available: [], locked: [] });
  const [loading, setLoading] = React.useState(true);
  const [expanded, setExpanded] = React.useState(true);

  React.useEffect(() => {
    if (!sessionId) return;
    const fetchTools = async () => {
      try {
        const res = await fetch(`${API_URL}/api/tools/available/${sessionId}`);
        const data = await res.json();
        if (data.status === 'success') {
          setTools({ available: data.available_tools, locked: data.locked_tools });
        }
      } catch (e) {
        console.error('Failed to fetch tools:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchTools();
  }, [sessionId]);

  const difficultyColors = {
    easy: 'from-green-500/20 to-emerald-500/20 border-green-500/40 text-green-400',
    medium: 'from-yellow-500/20 to-orange-500/20 border-yellow-500/40 text-yellow-400',
    hard: 'from-red-500/20 to-rose-500/20 border-red-500/40 text-red-400',
  };
  const diffBadge = difficultyColors[difficulty] || difficultyColors.easy;
  const allTools = [...tools.available, ...tools.locked];

  const [runningTool, setRunningTool] = useState(null);
  const [toolResult, setToolResult] = useState(null);
  const [showResultModal, setShowResultModal] = useState(false);

  // Custom modal states
  const [showSemgrepModal, setShowSemgrepModal] = useState(false);
  const [semgrepToolRef, setSemgrepToolRef] = useState(null);

  const executeToolApi = async (tool, payloadOptions = {}) => {
    setRunningTool(tool.id);
    try {
      let endpoint = tool.endpoint;
      let method = 'POST';
      let payload = { session_id: sessionId, ...payloadOptions };

      if (tool.id === 'vuln_hint' || tool.id === 'page_hint') {
        const firstVuln = vulnerabilities.find(v => v.enabled);
        if (!firstVuln) {
          alert("No vulnerabilities found to get a hint for.");
          setRunningTool(null);
          return;
        }
        endpoint = `hint/${sessionId}/${firstVuln.id}`;
        method = 'GET';
        payload = null;
      }
      else if (tool.id === 'http_inspector') {
        endpoint = `http-inspect/${sessionId}`;
        payload.target_url = payload.target_url || 'http://localhost:8080/search.php';
      }
      else if (['sqli_scanner', 'xss_scanner', 'zap_scanner'].includes(tool.id)) {
        payload.target_url = payload.target_url || 'http://localhost:8080/search.php';
      }

      console.log(`Running tool ${tool.id} with endpoint ${endpoint}...`);

      const requestOptions = {
        method: method,
        headers: { 'Content-Type': 'application/json' }
      };

      if (payload) {
        requestOptions.body = JSON.stringify(payload);
      }

      const response = await fetch(`${API_URL}/api/tools/${endpoint}`, requestOptions);
      const data = await response.json();
      setToolResult({ tool, data });
      setShowResultModal(true);
    } catch (err) {
      console.error("Tool execution failed:", err);
      alert(`Tool execution failed: ${err.message}`);
    } finally {
      setRunningTool(null);
    }
  };

  const runTool = async (tool) => {
    if (!tool.available) return;

    // Intercept Semgrep to show custom file modal
    if (tool.id === 'semgrep_sast') {
      setSemgrepToolRef(tool);
      setShowSemgrepModal(true);
      return;
    }

    // Otherwise run directly
    await executeToolApi(tool);
  };

  const handleSemgrepScan = async (targetFile) => {
    if (!semgrepToolRef) return;
    await executeToolApi(semgrepToolRef, { target_file: targetFile });
  };

  return (
    <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 mb-6">
      {/* Header */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-3 p-4 hover:bg-slate-800/30 rounded-2xl transition-all"
      >
        <div className="w-9 h-9 rounded-xl bg-orange-500/20 flex items-center justify-center">
          <Zap className="w-5 h-5 text-orange-400" />
        </div>
        <div className="flex-1 text-left">
          <h3 className="font-bold text-white text-sm">Security Tools</h3>
          <p className="text-xs text-gray-400">{tools.available.length} available · {tools.locked.length} locked</p>
        </div>
        <div className={`px-3 py-1 rounded-full bg-gradient-to-r border text-xs font-bold uppercase tracking-wider ${diffBadge}`}>
          {difficulty}
        </div>
        {expanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
      </button>

      {/* Tool Grid */}
      {expanded && (
        <div className="px-4 pb-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader className="w-6 h-6 animate-spin text-orange-400" />
            </div>
          ) : allTools.length === 0 ? (
            <p className="text-center text-gray-500 py-6 text-sm">No tools found for this session.</p>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {allTools.map(tool => {
                const isAvailable = tool.available;
                const isRunning = runningTool === tool.id;
                return (
                  <button
                    key={tool.id}
                    disabled={!isAvailable || isRunning}
                    onClick={() => runTool(tool)}
                    title={isAvailable ? tool.description : tool.locked_reason}
                    className={`relative p-3 rounded-xl border text-left transition-all group ${isAvailable
                      ? 'bg-slate-800/60 border-slate-600/50 hover:border-orange-500/50 hover:bg-slate-700/60'
                      : 'bg-slate-900/40 border-slate-700/30 opacity-50 cursor-not-allowed'
                      }`}
                  >
                    {/* Status icons */}
                    {!isAvailable ? (
                      <div className="absolute top-2 right-2">
                        <Lock className="w-3 h-3 text-gray-600" />
                      </div>
                    ) : isRunning ? (
                      <div className="absolute top-2 right-2">
                        <Loader className="w-3 h-3 text-orange-400 animate-spin" />
                      </div>
                    ) : null}

                    <div className="flex items-start gap-2">
                      <span className="text-xl leading-none mt-0.5" role="img">{tool.icon}</span>
                      <div className="min-w-0">
                        <p className={`text-xs font-semibold leading-tight truncate ${isAvailable ? 'text-white' : 'text-gray-600'
                          }`}>
                          {tool.name}
                        </p>
                        <p className="text-[10px] text-gray-500 mt-1 leading-tight line-clamp-2">
                          {isAvailable ? tool.description : tool.locked_reason}
                        </p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Tool Result Modal */}
          {showResultModal && toolResult && createPortal(
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
              <div className="bg-slate-900 border border-slate-700 rounded-3xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col shadow-2xl">
                <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{toolResult.tool.icon}</span>
                    <div>
                      <h3 className="font-bold text-white">{toolResult.tool.name} Results</h3>
                      <p className="text-xs text-gray-400">Scan completed successfully</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowResultModal(false)}
                    className="p-2 hover:bg-slate-800 rounded-xl transition-colors"
                  >
                    <XCircle className="w-6 h-6 text-gray-500 hover:text-white" />
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-6 bg-slate-950 font-mono text-sm">
                  {toolResult.data.status === 'error' ? (
                    <div className="text-red-400 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" />
                      <span>{toolResult.data.message}</span>
                    </div>
                  ) : (
                    <pre className="text-cyan-400 whitespace-pre-wrap">
                      {JSON.stringify(toolResult.data.result || toolResult.data.report || toolResult.data, null, 2)}
                    </pre>
                  )}
                </div>
                <div className="p-4 bg-slate-900 border-t border-slate-800 flex justify-end">
                  <button
                    onClick={() => setShowResultModal(false)}
                    className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-colors font-semibold"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>,
            document.body
          )}

          {/* Difficulty legend */}
          <div className="mt-3 pt-3 border-t border-slate-700/30 flex items-center gap-4 text-xs text-gray-500">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-green-500"></div><span>Unlocked</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Lock className="w-3 h-3" /><span>Locked on this difficulty</span>
            </div>
            <span className="ml-auto italic">
              {difficulty === 'easy' && 'All scanners available'}
              {difficulty === 'medium' && 'Scanners locked — hints only'}
              {difficulty === 'hard' && 'No automation — manual only'}
            </span>
          </div>
        </div>
      )}

      {/* Semgrep Custom File Modal */}
      <SemgrepModal
        isOpen={showSemgrepModal}
        onClose={() => setShowSemgrepModal(false)}
        sessionId={sessionId}
        onScan={handleSemgrepScan}
      />
    </div>
  );
};

// Animated Background Component
const CyberBackground = () => (
  <div className="fixed inset-0 overflow-hidden pointer-events-none opacity-20">
    <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500 rounded-full blur-3xl animate-pulse"></div>
    <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-pink-500 rounded-full blur-3xl animate-pulse delay-1000"></div>
    <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-cyan-500 rounded-full blur-3xl animate-pulse delay-2000"></div>
  </div>
);

// Severity Badge Component
const SeverityBadge = ({ severity }) => {
  const styles = {
    critical: 'bg-gradient-to-r from-red-600 to-red-700 shadow-lg shadow-red-500/50',
    high: 'bg-gradient-to-r from-orange-600 to-orange-700 shadow-lg shadow-orange-500/50',
    medium: 'bg-gradient-to-r from-yellow-600 to-yellow-700 shadow-lg shadow-yellow-500/50',
    low: 'bg-gradient-to-r from-blue-600 to-blue-700 shadow-lg shadow-blue-500/50'
  };
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${styles[severity]} animate-pulse`}>
      {severity.toUpperCase()}
    </span>
  );
};

// Glitch Text Effect
const GlitchText = ({ children, className = "" }) => (
  <div className={`relative ${className}`}>
    <span className="relative z-10">{children}</span>
    <span className="absolute top-0 left-0 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-600 animate-pulse opacity-70">
      {children}
    </span>
  </div>
);

// Main App Component
export default function HackOpsApp() {
  const [gameState, setGameState] = useState('menu');
  const [role, setRole] = useState(null);
  const [difficulty, setDifficulty] = useState('easy'); // NEW
  const [sessionId, setSessionId] = useState(null);
  const [seed, setSeed] = useState('');
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [score, setScore] = useState({ attacker: 0, defender: 0 });
  const [exploitedVulns, setExploitedVulns] = useState([]);
  const [defendedVulns, setDefendedVulns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [envStatus, setEnvStatus] = useState('offline'); // 'offline', 'starting', 'online'
  const [elapsedTime, setElapsedTime] = useState(0);
  // const [selectedVuln, setSelectedVuln] = useState(null);
  // const [showCodeModal, setShowCodeModal] = useState(false);
  const [sessionState, setSessionState] = useState(null);

  useEffect(() => {
    checkEnvironmentStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let interval;
    if (gameState === 'playing') {
      interval = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [gameState]);

  const checkEnvironmentStatus = async () => {
    try {
      const data = await api.getEnvironmentStatus();
      setEnvStatus(data.env_status || (data.is_running ? 'online' : 'offline'));
      
      // Auto-clear connection/startup errors if we successfully polled the status
      if (error && (error.includes('Cannot connect') || error.includes('Failed to start environment'))) {
        setError(null);
      }
    } catch (err) {
      // Only set error if we aren't already starting up or if it was a real connection lost
      setEnvStatus('offline');
      setError('Cannot connect to API. Make sure Flask server is running on port 5000.');
    }
  };

  // AI State
  const [aiEnabled, setAiEnabled] = useState(false);
  const [aiLastLog, setAiLastLog] = useState(null);

  // AI Loop
  useEffect(() => {
    let interval;
    if (aiEnabled && sessionState) {
      interval = setInterval(async () => {
        // Trigger AI Step
        try {
          // AI plays the OPPOSITE role
          const aiAgent = role === 'attacker' ? 'blue' : 'red';
          const response = await fetch(`${API_URL}/api/ai/step`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionState.session.session_id,
              agent: aiAgent
            })
          });

          const data = await response.json();
          if (data.status === 'success' && data.result) {
            const res = data.result;
            if (res.success) {
              // Format log message
              let logMsg = "";
              if (res.mapped_action) {
                logMsg = res.mapped_action.description || "Executed action";
                if (res.execution_result && !res.execution_result.success) {
                  logMsg += " (Failed)";
                }
              } else {
                logMsg = res.message || "Thinking...";
              }
              setAiLastLog(logMsg);

              // Refresh game state to reflect changes
              fetchSessionState(sessionState.session.session_id);
            }
          }
        } catch (e) {
          console.error("AI Step Error", e);
        }
      }, 5000); // Run every 5 seconds
    }
    return () => clearInterval(interval);
  }, [aiEnabled, sessionState, role]);

  const startGame = async () => {
    setLoading(true);
    setError(null);
    try {
      // Convert UI role names to API role names
      const apiRole = role === 'attacker' ? 'red' : 'blue';
      const data = await api.startEnvironment(seed || null, difficulty, apiRole);
      if (data.status === 'success') {
        setSessionId(data.session_id);
        setSeed(data.seed);

        const vulnData = await api.getVulnerabilities(data.session_id);
        setVulnerabilities(vulnData.vulnerabilities);

        setGameState('playing');
        setEnvStatus('online');
        setElapsedTime(0);
        addActivity('Game started - Systems online', 'info');
        fetchSessionState(data.session_id); // Fetch initial session state
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Failed to start environment: ' + err.message);
    }
    setLoading(false);
  };

  const stopGame = async () => {
    setLoading(true);
    try {
      await api.stopEnvironment();
      setGameState('results');
      setEnvStatus('offline');
      addActivity('Game ended - Systems shutting down', 'info');
    } catch (err) {
      setError('Failed to stop environment');
    }
    setLoading(false);
  };

  const fetchSessionState = async (id) => {
    try {
      const data = await api.getSession(id);
      if (data.status === 'success') {
        setSessionState(data);
        setScore(data.session.score);
        setExploitedVulns(data.session.exploits_found.map(e => e.vuln_id));
        setDefendedVulns(data.session.defenses_applied.map(d => d.vuln_id));
        setVulnerabilities(data.session.vulnerabilities); // Ensure vulnerabilities are up-to-date
      }
    } catch (err) {
      console.error("Failed to fetch session state:", err);
    }
  };

  // eslint-disable-next-line no-unused-vars
  const handleExploit = async (vuln) => {
    setLoading(true);
    try {
      const data = await api.reportExploit(sessionId, vuln.id, { method: 'manual', timestamp: Date.now() });
      if (data.status === 'success') {
        setScore(prev => ({ ...prev, attacker: data.total_score }));
        setExploitedVulns(prev => [...prev, vuln.id]);
        addActivity(`Exploited ${vuln.id} (+${data.points_awarded} pts)`, 'exploit');
        fetchSessionState(sessionId); // Refresh state after action
      } else {
        addActivity(data.message, 'info');
      }
    } catch (err) {
      setError('Failed to report exploit');
    }
    setLoading(false);
  };

  // eslint-disable-next-line no-unused-vars
  const handleDefend = async (vuln) => {
    setLoading(true);
    try {
      const data = await api.applyDefense(sessionId, vuln.id, vuln.fix_command);
      if (data.status === 'success') {
        setScore(prev => ({ ...prev, defender: data.total_score }));
        setDefendedVulns(prev => [...prev, vuln.id]);
        const bonus = data.proactive ? ' (Proactive!)' : '';
        addActivity(`Defended ${vuln.id} (+${data.points_awarded} pts)${bonus}`, 'defense');
        fetchSessionState(sessionId); // Refresh state after action
      } else {
        addActivity(data.message, 'info');
      }
    } catch (err) {
      setError('Failed to apply defense');
    }
    setLoading(false);
  };

  const addActivity = (message, type) => {
    // Activity feed UI was removed, just log to console
    console.log(`[Activity - ${type}]: ${message}`);
  };

  const resetGame = () => {
    setGameState('menu');
    setRole(null);
    setDifficulty('easy'); // Reset difficulty
    setSessionId(null);
    setSeed('');
    setVulnerabilities([]);
    setScore({ attacker: 0, defender: 0 });
    setExploitedVulns([]);
    setDefendedVulns([]);
    setElapsedTime(0);
    setError(null);
    setSessionState(null); // Reset session state
    setAiEnabled(false); // Reset AI
    setAiLastLog(null); // Reset AI log
    checkEnvironmentStatus(); // Refresh status when returning to menu
  };

  // Status Polling when in menu
  useEffect(() => {
    let interval;
    if (gameState === 'menu') {
      interval = setInterval(() => {
        checkEnvironmentStatus();
      }, 5000); // 5 seconds
    }
    return () => clearInterval(interval);
  }, [gameState]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Menu Screen
  if (gameState === 'menu') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white relative overflow-hidden">
        <CyberBackground />

        <div className="relative z-10 max-w-6xl mx-auto px-4 py-12">
          {/* Animated Header */}
          <div className="text-center mb-16">
            <div className="mb-6">
              <Terminal className="w-20 h-20 mx-auto text-cyan-400 animate-pulse" />
            </div>
            <GlitchText className="text-7xl font-black mb-4 bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
              HACKOPS
            </GlitchText>
            <p className="text-2xl text-gray-300 font-light tracking-wide">
              Elite Cybersecurity Training Platform
            </p>

            {/* Status Indicator */}
            <div className="mt-8 inline-flex items-center gap-3 px-6 py-3 rounded-full bg-slate-800/50 backdrop-blur-sm border border-slate-700">
              <div className={`relative w-4 h-4 rounded-full ${envStatus === 'online' ? 'bg-green-500' :
                  envStatus === 'starting' ? 'bg-orange-500' : 'bg-red-500'
                }`}>
                <div className={`absolute inset-0 rounded-full ${envStatus === 'online' ? 'bg-green-500' :
                    envStatus === 'starting' ? 'bg-orange-500' : 'bg-red-500'
                  } animate-ping opacity-75`}></div>
              </div>
              <span className={`text-xs font-bold uppercase tracking-wider ${envStatus === 'online' ? 'text-green-400' :
                  envStatus === 'starting' ? 'text-orange-400' : 'text-red-400'
                }`}>
                {envStatus === 'online' ? 'Environment Active' :
                  envStatus === 'starting' ? 'Environment Starting...' : 'Environment Offline'}
              </span>
              <Activity className="w-4 h-4 text-cyan-400" />
            </div>
          </div>

          {error && (
            <div className="mb-8 mx-auto max-w-2xl relative">
              <div className="bg-red-500/10 backdrop-blur-sm border border-red-500/50 rounded-2xl p-6 flex items-start gap-4 animate-slideIn">
                <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="font-bold text-red-400 mb-1">System Notice</h3>
                  <p className="text-sm text-gray-300">{error}</p>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="p-1 hover:bg-slate-800 rounded-lg text-gray-500 hover:text-white transition-colors"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          {/* Role Selection Cards */}
          <div className="grid md:grid-cols-2 gap-8 mb-12 max-w-5xl mx-auto">
            {/* Red Team Card (Coming Soon) */}
            <div className="group relative bg-gradient-to-br from-red-900/40 to-red-950/40 backdrop-blur-sm rounded-3xl p-8 border-2 border-red-500/10 transition-all duration-300 opacity-80 overflow-hidden cursor-not-allowed">
              <div className="absolute top-4 right-4 animate-pulse z-20">
                <span className="px-3 py-1 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-[10px] font-bold text-white uppercase tracking-wider shadow-lg shadow-purple-500/30">
                  Coming Soon
                </span>
              </div>
              
              <div className="absolute inset-0 bg-gradient-to-br from-red-500/0 to-red-500/5 rounded-3xl"></div>

              <div className="relative">
                <div className="mb-6 relative">
                  <div className="absolute inset-0 bg-red-500/10 blur-2xl rounded-full"></div>
                  <Sword className="w-20 h-20 mx-auto text-red-500/50 relative z-10" />
                </div>

                <h2 className="text-4xl font-bold mb-3 bg-gradient-to-r from-red-400/60 to-red-600/60 bg-clip-text text-transparent">
                  Red Team
                </h2>
                <p className="text-gray-400 mb-6 text-lg">
                  Infiltrate systems, exploit vulnerabilities, and dominate the battlefield.
                </p>

                <div className="space-y-3 text-left bg-slate-950/30 rounded-xl p-5 border border-red-500/10">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-red-500/30 rounded-full"></div>
                    <span className="text-sm text-gray-500">Discover & exploit vulnerabilities</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-red-500/30 rounded-full"></div>
                    <span className="text-sm text-gray-500">Critical: 100 | High: 50 | Medium: 25 | Low: 10</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-red-500/30 rounded-full"></div>
                    <span className="text-sm text-gray-500">Real-time attack simulation</span>
                  </div>
                </div>

                <div className="mt-6 inline-flex items-center gap-2 text-gray-500 font-semibold cursor-not-allowed">
                  <span>In Development</span>
                  <Activity className="w-5 h-5" />
                </div>
              </div>
            </div>

            {/* Blue Team Card */}
            <button
              onClick={() => { setRole('defender'); setGameState('setup'); }}
              className="group relative bg-gradient-to-br from-blue-900/50 to-blue-950/50 backdrop-blur-sm rounded-3xl p-8 border-2 border-blue-500/20 hover:border-blue-500/60 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/50"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/0 to-blue-500/10 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity"></div>

              <div className="relative">
                <div className="mb-6 relative">
                  <div className="absolute inset-0 bg-blue-500/20 blur-2xl rounded-full"></div>
                  <Shield className="w-20 h-20 mx-auto text-blue-500 relative z-10 transform group-hover:scale-110 transition-transform" />
                </div>

                <h2 className="text-4xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
                  Blue Team
                </h2>
                <p className="text-gray-300 mb-6 text-lg">
                  Fortify defenses, patch vulnerabilities, and protect the network.
                </p>

                <div className="space-y-3 text-left bg-slate-950/50 rounded-xl p-5 border border-blue-500/20">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm text-gray-300">Secure systems before exploitation</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm text-gray-300">Proactive: 30 | Reactive: 15 points</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm text-gray-300">Advanced threat detection</span>
                  </div>
                </div>

                <div className="mt-6 inline-flex items-center gap-2 text-blue-400 font-semibold">
                  <span>Deploy Defense</span>
                  <Shield className="w-5 h-5 group-hover:animate-pulse" />
                </div>
              </div>
            </button>
          </div>

          {/* <div className="text-center mt-8">
            <label className="inline-flex items-center gap-3 px-6 py-3 rounded-full bg-slate-800/30 backdrop-blur-sm border border-slate-700/50 cursor-pointer hover:border-purple-500/50 transition-all">
              <input
                type="checkbox"
                checked={rlMode}
                onChange={(e) => setRlMode(e.target.checked)}
                className="w-5 h-5 rounded"
              />
              <span className="text-sm text-gray-300">
                🤖 Enable RL Agent Mode (Train AI opponent)
              </span>
            </label>
          </div> */}

          {/* Footer Info */}
          {/* <div className="text-center">
            <div className="inline-flex items-center gap-3 px-6 py-3 rounded-full bg-slate-800/30 backdrop-blur-sm border border-slate-700/50">
              <div className="w-3 h-3 bg-purple-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-400">🤖 AI opponent training mode • Coming soon</span>
            </div>
          </div> */}
        </div>
      </div>
    );
  }

  // Setup Screen
  if (gameState === 'setup') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white relative overflow-hidden">
        <CyberBackground />

        <div className="relative z-10 max-w-3xl mx-auto px-4 py-12">
          <button
            onClick={() => setGameState('menu')}
            className="mb-8 flex items-center gap-2 text-gray-400 hover:text-white transition-colors group"
          >
            <div className="w-8 h-8 rounded-full bg-slate-800/50 flex items-center justify-center group-hover:bg-slate-700/50">
              ←
            </div>
            <span>Back to Menu</span>
          </button>

          <div className="bg-slate-900/50 backdrop-blur-xl rounded-3xl p-10 shadow-2xl border border-slate-700/50">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold mb-2 bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                Mission Setup
              </h2>
              <p className="text-gray-400">Configure your operation parameters</p>
            </div>

            {/* Role Display */}
            <div className="mb-8">
              <label className="block text-sm font-semibold mb-3 text-gray-300 uppercase tracking-wide">
                Selected Role
              </label>
              <div className={`p-6 rounded-2xl border-2 ${role === 'attacker'
                ? 'bg-gradient-to-r from-red-900/30 to-red-950/30 border-red-500/50'
                : 'bg-gradient-to-r from-blue-900/30 to-blue-950/30 border-blue-500/50'
                }`}>
                <div className="flex items-center gap-4">
                  {role === 'attacker' ? (
                    <>
                      <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center">
                        <Sword className="w-7 h-7 text-red-400" />
                      </div>
                      <div>
                        <div className="text-xl font-bold text-red-400">Red Team</div>
                        <div className="text-sm text-gray-400">Offensive Operations</div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                        <Shield className="w-7 h-7 text-blue-400" />
                      </div>
                      <div>
                        <div className="text-xl font-bold text-blue-400">Blue Team</div>
                        <div className="text-sm text-gray-400">Defensive Operations</div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Difficulty Selector */}
            <div className="mb-8">
              <label className="block text-sm font-semibold mb-3 text-gray-300 uppercase tracking-wide">
                Difficulty Level
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'easy', label: 'Easy', color: 'green', desc: 'SQLi Scanner + XSS Scanner + Hints', icon: '🟢' },
                  { id: 'medium', label: 'Medium', color: 'yellow', desc: 'Vuln Type Hints Only', icon: '🟡' },
                  { id: 'hard', label: 'Hard', color: 'red', desc: 'No Scanners — Manual Only', icon: '🔴' },
                ].map(d => (
                  <button
                    key={d.id}
                    onClick={() => setDifficulty(d.id)}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${difficulty === d.id
                      ? d.color === 'green' ? 'bg-green-900/40 border-green-500 shadow-lg shadow-green-500/20'
                        : d.color === 'yellow' ? 'bg-yellow-900/40 border-yellow-500 shadow-lg shadow-yellow-500/20'
                          : 'bg-red-900/40 border-red-500 shadow-lg shadow-red-500/20'
                      : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
                      }`}
                  >
                    <div className="text-xl mb-1">{d.icon}</div>
                    <div className={`font-bold text-sm mb-1 ${difficulty === d.id
                      ? d.color === 'green' ? 'text-green-400' : d.color === 'yellow' ? 'text-yellow-400' : 'text-red-400'
                      : 'text-gray-300'
                      }`}>{d.label}</div>
                    <div className="text-xs text-gray-500 leading-tight">{d.desc}</div>
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {difficulty === 'easy' && 'AI always uses its full toolset regardless of your difficulty.'}
                {difficulty === 'medium' && 'AI keeps full tools — you work with hints only. More challenge!'}
                {difficulty === 'hard' && 'AI at full strength while you have no auto-tools. Pure skill test!'}
              </p>
            </div>

            {/* Seed Input */}
            <div className="mb-8">
              <label className="block text-sm font-semibold mb-3 text-gray-300 uppercase tracking-wide">
                Mission Seed (Optional)
              </label>
              <input
                type="text"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                placeholder="Leave empty for random generation"
                className="w-full bg-slate-800/50 border-2 border-slate-700 rounded-xl px-5 py-4 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all placeholder-gray-500 text-white"
              />
              <p className="text-xs text-gray-500 mt-2 flex items-center gap-2">
                <Lock className="w-3 h-3" />
                Use identical seeds to replay specific scenarios
              </p>
            </div>

            {/* Start Button */}
            <button
              onClick={startGame}
              disabled={loading}
              className={`w-full py-5 rounded-xl font-bold text-lg transition-all transform hover:scale-105 disabled:scale-100 disabled:opacity-50 shadow-lg ${role === 'attacker'
                ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-red-500/50'
                : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-blue-500/50'
                }`}
            >
              {loading ? (
                <div className="flex items-center justify-center gap-3">
                  <Loader className="w-6 h-6 animate-spin" />
                  <span>Initializing Environment...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-3">
                  <Play className="w-6 h-6" />
                  <span>Launch Mission</span>
                </div>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Playing Screen
  if (gameState === 'playing') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white relative overflow-hidden">
        <CyberBackground />

        <EvasionLabModal />

        <div className="relative z-10 max-w-7xl mx-auto px-4 py-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6 bg-slate-900/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                HackOps Live
              </h1>
              <p className="text-gray-400 text-sm font-mono mt-1">Session: {sessionId}</p>
            </div>
            <button
              onClick={stopGame}
              className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-xl font-semibold flex items-center gap-2 transition-all transform hover:scale-105 shadow-lg shadow-red-500/50"
            >
              <Square className="w-4 h-4" />
              End Mission
            </button>
          </div>

          {error && (
            <div className="bg-red-500/10 backdrop-blur-sm border border-red-500/50 rounded-2xl p-4 mb-6 flex items-center justify-between gap-3 animate-slideIn">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <span className="text-sm">{error}</span>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-gray-500 hover:text-white transition-colors p-1"
              >
                ✕
              </button>
            </div>
          )}

          {/* ROW 1: Stats Bar */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl p-5 border border-slate-700/50 hover:border-cyan-500/50 transition-all">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-cyan-400" />
                </div>
                <span className="text-sm text-gray-400 font-medium">Mission Time</span>
              </div>
              <div className="text-3xl font-bold text-cyan-400">{formatTime(elapsedTime)}</div>
            </div>

            <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl p-5 border border-slate-700/50 hover:border-purple-500/50 transition-all">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
                  <Target className="w-5 h-5 text-purple-400" />
                </div>
                <span className="text-sm text-gray-400 font-medium">Vulnerabilities</span>
              </div>
              <div className="text-3xl font-bold text-purple-400">{vulnerabilities.filter(v => v.enabled).length}</div>
            </div>

            <div className={`bg-slate-900/50 backdrop-blur-xl rounded-2xl p-5 border transition-all ${role === 'attacker' ? 'border-red-500 shadow-lg shadow-red-500/20' : 'border-slate-700/50 hover:border-red-500/50'
              }`}>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center">
                  <Sword className="w-5 h-5 text-red-400" />
                </div>
                <span className="text-sm text-gray-400 font-medium">Red Team</span>
              </div>
              <div className="text-3xl font-bold text-red-400">{score.attacker}</div>
            </div>

            <div className={`bg-slate-900/50 backdrop-blur-xl rounded-2xl p-5 border transition-all ${role === 'defender' ? 'border-blue-500 shadow-lg shadow-blue-500/20' : 'border-slate-700/50 hover:border-blue-500/50'
              }`}>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-blue-400" />
                </div>
                <span className="text-sm text-gray-400 font-medium">Blue Team</span>
              </div>
              <div className="text-3xl font-bold text-blue-400">{score.defender}</div>
            </div>
          </div>

          {/* ROW 2: Logs & Intel */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <ActivityLogPanel sessionId={sessionId} />
            <AIAgentLogPanel sessionId={sessionId} />
            <MissionIntelPanel seed={seed} />
          </div>

          {/* ROW 2.5: Tools Panel */}
          <ToolsPanel
            sessionId={sessionId}
            role={role}
            difficulty={difficulty}
            vulnerabilities={vulnerabilities}
          />

          {/* ROW 3: Pages Grid */}
          <div className="mb-6">
            <PagesPanel sessionId={sessionId} />
          </div>

          {/* ROW 4: Main Console (Attacker/Defender) */}
          <div className="mb-24">
            {role === 'defender' ? (
              <DefenderView
                sessionId={sessionId}
                vulnerabilities={vulnerabilities}
                defendedVulns={defendedVulns}
                onUpdate={() => {
                  api.getSession(sessionId).then(data => {
                    if (data.status === 'success') {
                      setScore(data.session.score);
                      setDefendedVulns(data.session.defenses_applied.map(d => d.vuln_id));
                    }
                  });
                }}
              />
            ) : (
              <AttackerView
                sessionId={sessionId}
                vulnerabilities={vulnerabilities}
                exploitedVulns={exploitedVulns}
                onUpdate={() => {
                  api.getSession(sessionId).then(data => {
                    if (data.status === 'success') {
                      setScore(data.session.score);
                      setExploitedVulns(data.session.exploits_found.map(e => e.vuln_id));
                    }
                  });
                }}
              />
            )}
          </div>

          {/* Floating AI Control */}
          {sessionState && (
            <AIControlPanel
              enabled={aiEnabled}
              setEnabled={setAiEnabled}
              aiRole={role === 'attacker' ? 'Defender' : 'Attacker'}
              lastLog={aiLastLog}
            />
          )}
        </div>

        <style jsx>{`
          .custom-scrollbar::-webkit-scrollbar {
            width: 8px;
          }
          .custom-scrollbar::-webkit-scrollbar-track {
            background: rgba(51, 65, 85, 0.3);
            border-radius: 10px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(139, 92, 246, 0.5);
            border-radius: 10px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(139, 92, 246, 0.7);
          }
          @keyframes slideIn {
            from {
              opacity: 0;
              transform: translateX(-20px);
            }
            to {
              opacity: 1;
              transform: translateX(0);
            }
          }
          .animate-slideIn {
            animation: slideIn 0.3s ease-out;
          }
        `}</style>
      </div>
    );
  }

  // Results Screen
  if (gameState === 'results') {
    const winner = score.attacker > score.defender ? 'Red Team' : score.defender > score.attacker ? 'Blue Team' : 'Tie';
    const winnerColor = winner === 'Red Team' ? 'text-red-400' : winner === 'Blue Team' ? 'text-blue-400' : 'text-purple-400';

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white relative overflow-hidden">
        <CyberBackground />

        <div className="relative z-10 max-w-5xl mx-auto px-4 py-12">
          <div className="text-center mb-12">
            <div className="mb-6 relative">
              <div className="absolute inset-0 bg-yellow-500/20 blur-3xl"></div>
              <Trophy className="w-32 h-32 mx-auto text-yellow-400 relative z-10 animate-bounce" />
            </div>
            <h1 className="text-6xl font-black mb-4 bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
              MISSION COMPLETE
            </h1>
            <p className="text-3xl text-gray-300">
              Winner: <span className={`font-bold ${winnerColor}`}>{winner}</span>
            </p>
          </div>

          {/* Score Cards */}
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <div className="bg-gradient-to-br from-red-900/50 to-red-950/50 backdrop-blur-xl rounded-3xl p-8 border-2 border-red-500/30 transform hover:scale-105 transition-all">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-2xl bg-red-500/20 flex items-center justify-center">
                  <Sword className="w-10 h-10 text-red-400" />
                </div>
                <h2 className="text-3xl font-bold text-red-400">Red Team</h2>
              </div>
              <div className="text-7xl font-black mb-6 text-red-400">{score.attacker}</div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between p-3 bg-slate-900/50 rounded-lg">
                  <span className="text-gray-300">Exploited</span>
                  <span className="text-red-400 font-bold">{exploitedVulns.length}/{vulnerabilities.filter(v => v.enabled).length}</span>
                </div>
                <div className="flex justify-between p-3 bg-slate-900/50 rounded-lg">
                  <span className="text-gray-300">Success Rate</span>
                  <span className="text-red-400 font-bold">
                    {vulnerabilities.filter(v => v.enabled).length > 0 ? Math.round((exploitedVulns.length / vulnerabilities.filter(v => v.enabled).length) * 100) : 0}%
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-900/50 to-blue-950/50 backdrop-blur-xl rounded-3xl p-8 border-2 border-blue-500/30 transform hover:scale-105 transition-all">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-2xl bg-blue-500/20 flex items-center justify-center">
                  <Shield className="w-10 h-10 text-blue-400" />
                </div>
                <h2 className="text-3xl font-bold text-blue-400">Blue Team</h2>
              </div>
              <div className="text-7xl font-black mb-6 text-blue-400">{score.defender}</div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between p-3 bg-slate-900/50 rounded-lg">
                  <span className="text-gray-300">Defended</span>
                  <span className="text-blue-400 font-bold">{defendedVulns.length}/{vulnerabilities.filter(v => v.enabled).length}</span>
                </div>
                <div className="flex justify-between p-3 bg-slate-900/50 rounded-lg">
                  <span className="text-gray-300">Protection Rate</span>
                  <span className="text-blue-400 font-bold">
                    {vulnerabilities.filter(v => v.enabled).length > 0 ? Math.round((defendedVulns.length / vulnerabilities.filter(v => v.enabled).length) * 100) : 0}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Statistics */}
          <div className="bg-slate-900/50 backdrop-blur-xl rounded-3xl p-8 border border-slate-700/50 mb-8">
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
              <Activity className="w-6 h-6 text-purple-400" />
              Mission Statistics
            </h3>
            <div className="grid grid-cols-3 gap-6 text-center">
              <div className="p-6 bg-slate-800/50 rounded-2xl border border-slate-700/50">
                <div className="text-5xl font-bold text-cyan-400 mb-2">{formatTime(elapsedTime)}</div>
                <div className="text-sm text-gray-400">Mission Duration</div>
              </div>
              <div className="p-6 bg-slate-800/50 rounded-2xl border border-slate-700/50">
                <div className="text-5xl font-bold text-purple-400 mb-2">{vulnerabilities.filter(v => v.enabled).length}</div>
                <div className="text-sm text-gray-400">Active Vulnerabilities</div>
              </div>
              <div className="p-6 bg-slate-800/50 rounded-2xl border border-slate-700/50">
                <div className="text-5xl font-bold text-pink-400 mb-2">{exploitedVulns.length + defendedVulns.length}</div>
                <div className="text-sm text-gray-400">Total Actions</div>
              </div>
            </div>
          </div>

          {/* Play Again Button */}
          <button
            onClick={resetGame}
            className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-cyan-600 rounded-2xl py-5 font-bold text-xl hover:from-purple-700 hover:via-pink-700 hover:to-cyan-700 transition-all transform hover:scale-105 shadow-2xl shadow-purple-500/50"
          >
            <div className="flex items-center justify-center gap-3">
              <Play className="w-6 h-6" />
              Start New Mission
            </div>
          </button>
        </div>
      </div>
    );
  }

  return null;
}