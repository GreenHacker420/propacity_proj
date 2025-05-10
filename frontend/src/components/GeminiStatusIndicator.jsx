
import { motion } from 'framer-motion';
import { BoltIcon, ClockIcon, ExclamationTriangleIcon, ServerIcon, ShieldCheckIcon } from '@heroicons/react/24/solid';
import useGeminiStatus from '../hooks/useGeminiStatus';

const GeminiStatusIndicator = ({ className = '', refreshInterval = 10000 }) => {
  // Use the custom hook for Gemini status
  const {
    status,
    loading,
    timeRemaining,
    formatTime,
    isLimited
  } = useGeminiStatus(refreshInterval);

  if (loading) return null;

  // If everything is normal, don't show anything
  if (!isLimited) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className={`bg-gradient-to-r ${
        status?.circuit_open
          ? 'from-orange-50 to-orange-100 border-orange-200'
          : status?.rate_limited
            ? 'from-amber-50 to-amber-100 border-amber-200'
            : 'from-red-50 to-red-100 border-red-200'
      } rounded-lg p-4 shadow-md border ${className}`}
    >
      <div className="flex items-center space-x-3">
        <div className="flex-shrink-0">
          <div className={`p-2 rounded-full ${
            status?.circuit_open
              ? 'bg-orange-100'
              : status?.rate_limited
                ? 'bg-amber-100'
                : 'bg-red-100'
          }`}>
            {status?.circuit_open ? (
              <ShieldCheckIcon className="h-6 w-6 text-orange-600" />
            ) : status?.rate_limited ? (
              <BoltIcon className="h-6 w-6 text-amber-600" />
            ) : (
              <ServerIcon className="h-6 w-6 text-red-600" />
            )}
          </div>
        </div>
        <div className="flex-1">
          <h3 className={`text-sm font-medium ${
            status?.circuit_open
              ? 'text-orange-800'
              : status?.rate_limited
                ? 'text-amber-800'
                : 'text-red-800'
          }`}>
            {status?.circuit_open
              ? 'Circuit Breaker Active'
              : status?.rate_limited
                ? 'API Rate Limit Reached'
                : 'Gemini API Unavailable'}
          </h3>
          <div className={`mt-1 text-xs ${
            status?.circuit_open
              ? 'text-orange-700'
              : status?.rate_limited
                ? 'text-amber-700'
                : 'text-red-700'
          }`}>
            {status?.circuit_open && (
              <div className="flex items-center">
                <ExclamationTriangleIcon className="h-4 w-4 text-orange-500 mr-1" />
                <span>
                  Circuit breaker is open due to repeated API failures
                </span>
              </div>
            )}

            {status?.rate_limited && (
              <div className="flex items-center">
                <ExclamationTriangleIcon className="h-4 w-4 text-amber-500 mr-1" />
                <span>
                  Gemini API rate limit reached
                </span>
              </div>
            )}

            {!status?.available && !status?.circuit_open && !status?.rate_limited && (
              <div className="flex items-center">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-500 mr-1" />
                <span>
                  Gemini API is currently unavailable
                </span>
              </div>
            )}

            {/* Time remaining for circuit breaker */}
            {status?.circuit_open && timeRemaining.circuit > 0 && (
              <div className="flex items-center mt-1">
                <ClockIcon className="h-4 w-4 text-orange-500 mr-1" />
                <span>
                  Circuit resets in: <span className="font-medium">{formatTime(timeRemaining.circuit)}</span>
                </span>
              </div>
            )}

            {/* Time remaining for rate limit */}
            {status?.rate_limited && timeRemaining.rateLimit > 0 && (
              <div className="flex items-center mt-1">
                <ClockIcon className="h-4 w-4 text-amber-500 mr-1" />
                <span>
                  Rate limit resets in: <span className="font-medium">{formatTime(timeRemaining.rateLimit)}</span>
                </span>
              </div>
            )}

            {/* Model info */}
            {status?.model && (
              <div className="mt-2 flex items-center">
                <ServerIcon className="h-4 w-4 text-gray-500 mr-1" />
                <span>
                  Model: <span className="font-medium">{status.model}</span>
                </span>
              </div>
            )}

            <div className="mt-2 text-xs">
              <span className="font-medium">Note:</span> The system is automatically using local processing methods.
            </div>
          </div>
        </div>
      </div>

      {/* Progress bar for circuit breaker */}
      {status?.circuit_open && timeRemaining.circuit > 0 && status?.circuit_reset_in && (
        <div className="mt-2 bg-white rounded-full h-1.5 overflow-hidden">
          <motion.div
            className="bg-orange-500 h-full"
            initial={{ width: '100%' }}
            animate={{ width: `${(timeRemaining.circuit / status.circuit_reset_in) * 100}%` }}
            transition={{ duration: 1, ease: 'linear' }}
          />
        </div>
      )}

      {/* Progress bar for rate limit */}
      {status?.rate_limited && timeRemaining.rateLimit > 0 && status?.rate_limit_reset_in && (
        <div className="mt-2 bg-white rounded-full h-1.5 overflow-hidden">
          <motion.div
            className="bg-amber-500 h-full"
            initial={{ width: '100%' }}
            animate={{ width: `${(timeRemaining.rateLimit / status.rate_limit_reset_in) * 100}%` }}
            transition={{ duration: 1, ease: 'linear' }}
          />
        </div>
      )}
    </motion.div>
  );
};

export default GeminiStatusIndicator;
