import time
import threading
from typing import Callable, Optional


class AutoSender:
    """Handles auto-sending with cancellation buffer"""
    
    def __init__(self):
        self.cancelled = False
        self.countdown_active = False
    
    def send_with_buffer(
        self,
        buffer_seconds: int,
        send_function: Callable,
        on_countdown: Optional[Callable[[int], None]] = None,
        on_cancel: Optional[Callable] = None,
        on_send: Optional[Callable] = None
    ):
        
        self.cancelled = False
        self.countdown_active = True
        
        # Countdown
        for remaining in range(buffer_seconds, 0, -1):
            if self.cancelled:
                if on_cancel:
                    on_cancel()
                self.countdown_active = False
                return False
            
            if on_countdown:
                on_countdown(remaining)
            
            time.sleep(1)
        
        # Send if not cancelled
        if not self.cancelled:
            result = send_function()
            self.countdown_active = False
            
            if on_send:
                on_send()
            
            return result
        
        self.countdown_active = False
        return False
    
    def cancel(self):
        """Cancel the pending send"""
        self.cancelled = True
    
    def is_active(self):
        """Check if countdown is active"""
        return self.countdown_active


def send_immediately(send_function: Callable) -> bool:
    """Send message immediately without buffer"""
    try:
        return send_function()
    except Exception as e:
        print(f"Error sending: {e}")
        return False