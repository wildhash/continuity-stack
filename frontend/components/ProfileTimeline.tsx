import { useState, useEffect } from 'react';
import { apiClient, AgentStatus } from '../lib/api';

interface TimelineEvent {
  id: string;
  timestamp: string;
  type: 'task' | 'reflection' | 'capability' | 'lesson';
  title: string;
  description: string;
  status?: string;
}

export default function ProfileTimeline() {
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTimeline();
    const interval = setInterval(loadTimeline, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadTimeline = async () => {
    try {
      const [status, history] = await Promise.all([
        apiClient.getAgentStatus(),
        apiClient.getAgentHistory(),
      ]);

      setAgentStatus(status);

      const timelineEvents: TimelineEvent[] = [];

      // Add task events
      history.tasks.forEach((task: any) => {
        timelineEvents.push({
          id: task.task_id,
          timestamp: task.timestamp,
          type: 'task',
          title: `Task: ${task.task_type}`,
          description: task.status === 'failed' ? task.error : 'Completed successfully',
          status: task.status,
        });
      });

      // Add reflection events
      history.reflections.forEach((reflection: any) => {
        timelineEvents.push({
          id: reflection.task_id + '_reflection',
          timestamp: reflection.timestamp,
          type: 'reflection',
          title: 'Reflection & Learning',
          description: reflection.lesson_learned || 'Analyzing task outcome',
          status: 'completed',
        });
      });

      // Add capability events
      status.capabilities.forEach((capability: string, index: number) => {
        timelineEvents.push({
          id: `capability_${index}`,
          timestamp: new Date().toISOString(),
          type: 'capability',
          title: `Capability: ${capability}`,
          description: 'New capability acquired',
        });
      });

      // Sort by timestamp (newest first)
      timelineEvents.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );

      setEvents(timelineEvents);
    } catch (error) {
      console.error('Error loading timeline:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'task':
        return '⚡';
      case 'reflection':
        return '🧠';
      case 'capability':
        return '🎯';
      case 'lesson':
        return '📚';
      default:
        return '•';
    }
  };

  const getEventColor = (type: string, status?: string) => {
    if (status === 'failed') return 'border-red-500 bg-red-50';
    if (status === 'success') return 'border-green-500 bg-green-50';
    switch (type) {
      case 'reflection':
        return 'border-purple-500 bg-purple-50';
      case 'capability':
        return 'border-blue-500 bg-blue-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Loading timeline...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 h-full overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Agent Profile</h2>
        {agentStatus && (
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-lg">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm opacity-90">Version</p>
                <p className="text-xl font-bold">{agentStatus.version}</p>
              </div>
              <div>
                <p className="text-sm opacity-90">Capabilities</p>
                <p className="text-xl font-bold">{agentStatus.capabilities.length}</p>
              </div>
              <div>
                <p className="text-sm opacity-90">Tasks</p>
                <p className="text-xl font-bold">{agentStatus.total_tasks}</p>
              </div>
              <div>
                <p className="text-sm opacity-90">Lessons</p>
                <p className="text-xl font-bold">{agentStatus.learned_lessons.length}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Timeline</h3>
      </div>

      <div className="space-y-4">
        {events.map((event, index) => (
          <div key={event.id} className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-gray-200 rounded-full text-lg">
              {getEventIcon(event.type)}
            </div>
            <div className={`flex-1 border-l-4 pl-4 py-2 ${getEventColor(event.type, event.status)}`}>
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-gray-900">{event.title}</h4>
                  <p className="text-sm text-gray-700 mt-1">{event.description}</p>
                </div>
                <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                  {new Date(event.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        ))}

        {events.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <p>No events yet. Start a conversation to see the agent in action!</p>
          </div>
        )}
      </div>
    </div>
  );
}
