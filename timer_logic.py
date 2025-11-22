import time
import threading
import datetime
from system_utils import IdleMonitor

class Timer:
    def __init__(self, sitting_duration=25, standing_duration=5, transition_duration=30,
                 work_schedules=["08:00-17:00"], 
                 idle_threshold_mins=5,
                 on_tick=None, on_finish=None, on_idle_reset=None):
        
        self.sitting_duration = sitting_duration * 60
        self.standing_duration = standing_duration * 60
        self.transition_duration = transition_duration # Seconds
        
        self.current_duration = self.sitting_duration
        self.remaining_time = self.current_duration
        self.is_running = False
        self.mode = "Sitting" # Sitting, Standing, Transition
        self.next_mode = "Standing" # Used during transition
        
        # Advanced Settings
        self.work_schedules = work_schedules # List of strings "HH:MM-HH:MM"
        self.idle_threshold_seconds = idle_threshold_mins * 60
        self.idle_monitor = IdleMonitor()
        
        self.on_tick = on_tick
        self.on_finish = on_finish
        self.on_idle_reset = on_idle_reset
        
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            # Create a NEW event for this run session to avoid race conditions with old threads
            self._stop_event = threading.Event()
            self._thread = threading.Thread(target=self._run, args=(self._stop_event,))
            self._thread.daemon = True
            self._thread.start()

    def pause(self):
        self.is_running = False
        self._stop_event.set()

    def reset(self):
        self.pause()
        # Reset to start of current main mode (skip transition if we were in it?)
        # If in transition, maybe reset to the mode we were transitioning TO?
        # Or just reset to Sitting. Let's reset to Sitting for simplicity or current main mode.
        if self.mode == "Transition":
            self.mode = self.next_mode
            
        if self.mode == "Sitting":
            self.current_duration = self.sitting_duration
        else:
            self.current_duration = self.standing_duration
            
        self.remaining_time = self.current_duration
        if self.on_tick:
            self.on_tick(self.remaining_time)

    def skip(self):
        self.pause()
        self._switch_mode()
        if self.on_tick:
            self.on_tick(self.remaining_time)

    def update_settings(self, sitting_minutes, standing_minutes, transition_seconds, schedules, idle_mins):
        self.sitting_duration = sitting_minutes * 60
        self.standing_duration = standing_minutes * 60
        self.transition_duration = transition_seconds
        self.work_schedules = schedules
        self.idle_threshold_seconds = idle_mins * 60
        
        if not self.is_running:
             self.reset()

    def _switch_mode(self):
        if self.mode == "Sitting":
            self.mode = "Transition"
            self.next_mode = "Standing"
            self.current_duration = self.transition_duration
        elif self.mode == "Standing":
            self.mode = "Transition"
            self.next_mode = "Sitting"
            self.current_duration = self.transition_duration
        elif self.mode == "Transition":
            self.mode = self.next_mode
            if self.mode == "Sitting":
                self.current_duration = self.sitting_duration
            else:
                self.current_duration = self.standing_duration
        
        self.remaining_time = self.current_duration

    def _is_within_work_hours(self):
        if not self.work_schedules:
            return True
            
        now = datetime.datetime.now()
        current_min = now.hour * 60 + now.minute
        
        for schedule in self.work_schedules:
            try:
                start_str, end_str = schedule.split('-')
                sh, sm = map(int, start_str.split(':'))
                eh, em = map(int, end_str.split(':'))
                
                start_min = sh * 60 + sm
                end_min = eh * 60 + em
                
                if start_min < end_min:
                    # Standard day range
                    if start_min <= current_min < end_min:
                        return True
                else:
                    # Overnight range
                    if current_min >= start_min or current_min < end_min:
                        return True
            except:
                continue # Ignore invalid formats
                
        return False

    def _run(self, stop_event):
        while self.is_running and not stop_event.is_set():
            time.sleep(1)
            
            if not self.is_running or stop_event.is_set():
                break

            # 1. Check Work Hours (Only if NOT in transition - force transition to finish?)
            # Or pause transition too? Let's pause everything outside work hours.
            if not self._is_within_work_hours():
                continue

            # 2. Check Idle (Only in Sitting mode)
            if self.mode == "Sitting":
                idle_sec = self.idle_monitor.get_idle_duration()
                if idle_sec > self.idle_threshold_seconds:
                    self.remaining_time = self.sitting_duration
                    if self.on_idle_reset:
                        self.on_idle_reset()
                    if self.on_tick:
                        self.on_tick(self.remaining_time)
                    continue

            # 3. Countdown
            self.remaining_time -= 1
            if self.on_tick:
                self.on_tick(self.remaining_time)

            if self.remaining_time <= 0:
                self.is_running = False
                self._switch_mode()
                if self.on_finish:
                    self.on_finish(self.mode)
                # Auto-start next mode?
                # Yes, usually timers flow automatically.
                # Especially Transition -> Mode.
                # But Mode -> Transition might need user acknowledgement? 
                # User said "Strict mode... during transition". So it should auto-enter transition.
                self.start()
                break
