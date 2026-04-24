/**
 * Component: Tooltip
 * Hover tooltip display
 */

import React, { useState, useRef } from 'react';
import './Tooltip.css';

export function Tooltip({ 
  children, 
  content,
  position = 'top',
  delay = 200,
}) {
  const [visible, setVisible] = useState(false);
  const timeoutId = useRef(null);

  const handleMouseEnter = () => {
    timeoutId.current = setTimeout(() => setVisible(true), delay);
  };

  const handleMouseLeave = () => {
    clearTimeout(timeoutId.current);
    setVisible(false);
  };

  return (
    <div 
      className="tooltip-wrapper"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {visible && (
        <div className={`tooltip tooltip--${position}`}>
          <div className="tooltip__content">{content}</div>
          <div className="tooltip__arrow"></div>
        </div>
      )}
    </div>
  );
}
