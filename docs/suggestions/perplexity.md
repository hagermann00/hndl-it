# Perplexity Suggestions for hndl-it

## Date: 2026-01-10

---

## Executive Assessment

Your hndl-it project demonstrates sophisticated architectural thinking with solid modular scaffolding. The system achieves approximately **85% structural completion, 15% operational integration**. Individual components (Browser Agent, Desktop Agent, Vision pipeline, Floater UI) function correctly in isolation, but the critical missing piece is a **central orchestration layer** that routes commands intelligently and manages state across agents. This document focuses on closing that gap and creating the foundation for sustainable monetization.

Your hardware constraints (i7-8700, RTX 2060 12GB) are actually advantageous—they force architectural decisions that scale better than over-provisioned systems. The Y-IT use case is excellent: it demonstrates system value immediately while creating recurring revenue.

---

## Priority 1: Orchestration Architecture - The Foundation

### Problem Statement

Current state: `run.py` spawns independent processes that listen on WebSocket ports but have no shared context or intelligent routing. The floater UI sends commands directly to agents without classification logic or error handling.

**Result**: The system is 80% "hands" (agents) and 20% "brain" (orchestration). Adding todo-it or voice just creates more disconnected modules.

### Solution: Central Orchestrator Pattern

Create `shared/orchestrator.py` as the intelligent middleware:

```python
# shared/orchestrator.py
import asyncio
import json
import logging
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import websockets
from abc import ABC, abstractmethod

class AgentType(Enum):
    """Supported agent types"""
    BROWSER = "browser"
    DESKTOP = "desktop"
    VISION = "vision"
    MEMORY = "memory"
    VOICE = "voice"

@dataclass
class Command:
    """Classified user command"""
    agent: AgentType
    action: str
    params: Dict
    confidence: float = 1.0
    raw_input: str = ""
    timestamp: str = ""

class CommandClassifier:
    """Intent classification engine - regex first, LLM fallback"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.rules = self._build_rules()
    
    def _build_rules(self) -> Dict[AgentType, List[Tuple[str, str]]]:
        """Regex patterns for fast classification"""
        return {
            AgentType.BROWSER: [
                (r'^(go to|open|navigate to)\s+(.+)', 'navigate'),
                (r'^(click|find|search)\s+(.+)', 'click'),
                (r'^scroll\s+(up|down|top|bottom)', 'scroll'),
                (r'^(back|forward|refresh)', 'back'),
                (r'^scrape(.+)?$', 'scrape'),
            ],
            AgentType.DESKTOP: [
                (r'^(list|ls|show)\s+(.+)', 'list'),
                (r'^(open|execute|run)\s+(.+)', 'open'),
                (r'^(delete|remove)\s+(.+)', 'delete'),
                (r'^screenshot', 'screenshot'),
            ],
            AgentType.VISION: [
                (r'^(where|find|locate)\s+(.+)', 'locate'),
                (r'^(read|extract|ocr)\s+(.+)', 'extract'),
                (r'^(describe|analyze|what is)\s+(.+)', 'describe'),
            ],
            AgentType.MEMORY: [
                (r'^(remember|save|store)\s+(.+)', 'save'),
                (r'^(recall|remind|what did)\s+(.+)', 'recall'),
                (r'^(task|todo|remember)\s+(.+)', 'task'),
            ]
        }
    
    def classify(self, user_input: str) -> Command:
        """Classify user input using regex patterns"""
        user_input = user_input.strip()
        
        for agent_type, patterns in self.rules.items():
            for pattern, action in patterns:
                import re
                match = re.match(pattern, user_input, re.IGNORECASE)
                if match:
                    params = {}
                    if match.groups():
                        # Extract parameters from regex groups
                        params = {"input": match.group(2) if len(match.groups()) > 1 else match.group(1)}
                    
                    return Command(
                        agent=agent_type,
                        action=action,
                        params=params,
                        confidence=0.95,
                        raw_input=user_input,
                        timestamp=datetime.now().isoformat()
                    )
        
        # Low confidence - will trigger LLM fallback in orchestrator
        return Command(
            agent=AgentType.MEMORY,
            action="help",
            params={"input": user_input},
            confidence=0.3,
            raw_input=user_input,
            timestamp=datetime.now().isoformat()
        )
    
    async def classify_with_llm(self, user_input: str) -> Command:
        """Use Ollama for complex intent classification"""
        prompt = f"""Parse this user command into JSON. Be strict with format.

User input: "{user_input}"

Return ONLY valid JSON with these fields:
- agent: one of [browser, desktop, vision, memory, voice]
- action: specific action name
- params: object with extracted parameters

Example response:
{{"agent": "browser", "action": "navigate", "params": {{"url": "reddit.com"}}}}

JSON:"""
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "qwen2.5:7b",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                response_text = response.json()["response"]
                
                # Extract JSON from response
                import re
                json_match = re.search(r'\{[^{}]*\}', response_text)
                if json_match:
                    data = json.loads(json_match.group())
                    return Command(
                        agent=AgentType[data["agent"].upper()],
                        action=data.get("action", "unknown"),
                        params=data.get("params", {}),
                        confidence=0.75,
                        raw_input=user_input,
                        timestamp=datetime.now().isoformat()
                    )
        except Exception as e:
            logging.warning(f"LLM classification failed: {e}")
        
        return Command(
            agent=AgentType.MEMORY,
            action="clarify",
            params={"input": user_input},
            confidence=0.2,
            raw_input=user_input,
            timestamp=datetime.now().isoformat()
        )

class Orchestrator:
    """Central command orchestration engine"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.agents = config.get("agents", {})
        self.classifier = CommandClassifier(config.get("ollama_url"))
        self.history: List[Dict] = []
        self.logger = logging.getLogger("Orchestrator")
        self.llm_confidence_threshold = config.get("llm_threshold", 0.7)
    
    async def process(self, user_input: str) -> Dict:
        """Main entry point - process user input end-to-end"""
        execution_id = self._generate_id()
        start_time = datetime.now()
        
        try:
            self.logger.info(f"[{execution_id}] Processing: {user_input}")
            
            # Step 1: Classify intent
            command = self.classifier.classify(user_input)
            
            # Step 2: If low confidence, use LLM fallback
            if command.confidence < self.llm_confidence_threshold:
                self.logger.info(f"[{execution_id}] Low confidence ({command.confidence:.2f}), using LLM")
                command = await self.classifier.classify_with_llm(user_input)
            
            # Step 3: Route to appropriate agent
            result = await self._execute_command(command, execution_id)
            
            # Step 4: Record execution
            execution_time = (datetime.now() - start_time).total_seconds()
            record = {
                "id": execution_id,
                "input": user_input,
                "command": asdict(command),
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            self.history.append(record)
            
            self.logger.info(f"[{execution_id}] Success ({execution_time:.2f}s)")
            
            return {
                "success": True,
                "result": result,
                "execution_id": execution_id
            }
            
        except Exception as e:
            self.logger.error(f"[{execution_id}] Error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "execution_id": execution_id
            }
    
    async def _execute_command(self, command: Command, execution_id: str) -> str:
        """Route command to appropriate agent"""
        
        if command.agent == AgentType.MEMORY:
            return await self._handle_memory_command(command)
        
        agent_url = self.agents.get(command.agent.value)
        if not agent_url:
            raise ValueError(f"No agent configured for {command.agent.value}")
        
        try:
            async with websockets.connect(agent_url) as ws:
                # Send command to agent
                message = {
                    "type": "command",
                    "action": command.action,
                    "params": command.params,
                    "execution_id": execution_id
                }
                
                self.logger.debug(f"[{execution_id}] Sending to {command.agent.value}: {message}")
                await ws.send(json.dumps(message))
                
                # Wait for response with timeout
                response_text = await asyncio.wait_for(ws.recv(), timeout=30.0)
                response = json.loads(response_text)
                
                self.logger.debug(f"[{execution_id}] Response: {response}")
                
                return response.get("content", "No response from agent")
        
        except asyncio.TimeoutError:
            raise TimeoutError(f"{command.agent.value} agent did not respond within 30 seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to execute on {command.agent.value}: {str(e)}")
    
    async def _handle_memory_command(self, command: Command) -> str:
        """Handle memory/local operations"""
        action = command.action
        
        if action == "help":
            return self._get_help_text(command.params.get("input"))
        elif action == "clarify":
            return f"I didn't understand '{command.params.get('input')}'. Try: 'open google', 'click submit', 'list downloads', etc."
        else:
            return "Memory command not implemented"
    
    def _get_help_text(self, context: str = "") -> str:
        """Generate contextual help"""
        return """Available commands:
Browser: 'go to [url]', 'click [element]', 'scroll [direction]', 'scrape'
Desktop: 'list [path]', 'open [file]', 'screenshot'
Vision: 'where [object]', 'read [image]', 'describe [scene]'
Memory: 'remember [task]', 'remind me', 'what did I...'
"""
    
    def _generate_id(self) -> str:
        """Generate execution ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Retrieve execution history"""
        return self.history[-limit:]
    
    def clear_history(self):
        """Clear execution history"""
        self.history = []

# Singleton instance
_orchestrator = None

def get_orchestrator(config: Dict = None) -> Orchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator(config or {})
    return _orchestrator
```

### Integration with Floater UI

Modify `floater/main.py`:

```python
# In floater/main.py
from shared.orchestrator import get_orchestrator

class FloaterApp:
    def __init__(self):
        # ... existing code ...
        self.orchestrator = get_orchestrator({
            "agents": {
                "browser": "ws://localhost:8766",
                "desktop": "ws://localhost:8767",
                "vision": "ws://localhost:8768"
            },
            "ollama_url": self.config.get("ollama_url", "http://localhost:11434"),
            "llm_threshold": 0.7
        })
    
    async def handle_command_input(self, user_input: str):
        """Process user input through orchestrator"""
        self.status_label.setText("Processing...")
        
        result = await self.orchestrator.process(user_input)
        
        if result["success"]:
            self.display_result(result["result"])
        else:
            self.display_error(result.get("error", "Unknown error"))
        
        self.status_label.setText("Ready")
```

### Why This Architecture Works

1. **Single Point of Intelligence**: One location for command classification logic; easy to update
2. **Graceful Degradation**: Regex fast-path for common commands; LLM fallback for complex ones
3. **Execution Visibility**: Complete history of what executed, when, and with what result
4. **Extensibility**: New agents plug in automatically; no floater UI changes needed
5. **Error Handling**: Centralized timeout, retry, and error recovery logic
6. **Agent Independence**: Agents remain stateless; orchestrator manages workflow state

---

## Priority 2: Voice Integration - Speech-to-Text Pipeline

### Current State

Your VOICE_INPUT_ARCHITECTURE.md references Python SpeechRecognition library. This is suboptimal for local-first systems:
- Requires internet for decent accuracy
- Slow (~2-3 seconds latency)
- Adds cloud dependency (contradicts hndl-it philosophy)

### Recommended: Whisper.cpp (C++ Port)

Replace with local Whisper.cpp:

```python
# shared/voice_input.py
import asyncio
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import sounddevice as sd
import scipy.io.wavfile as wavfile
import webrtcvad

try:
    from pywhispercpp.model import Model
except ImportError:
    print("Install: pip install pywhispercpp sounddevice scipy webrtcvad")

class VoiceInput:
    """Local speech-to-text with silence detection"""
    
    def __init__(self, model_size: str = "base.en"):
        """
        Initialize Whisper model
        
        Args:
            model_size: "tiny.en", "base.en", "small.en", "medium.en"
                       For 12GB VRAM, "base.en" is optimal (140MB, good accuracy)
        """
        self.logger = logging.getLogger("VoiceInput")
        self.model = Model(model_size)
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)  # Most aggressive silence detection
        
        # Audio parameters
        self.SAMPLE_RATE = 16000
        self.CHUNK_DURATION_MS = 30  # Must be 10, 20, or 30
        self.CHUNK_SIZE = (self.SAMPLE_RATE // 1000) * self.CHUNK_DURATION_MS
        self.SILENCE_THRESHOLD = 1.0  # Seconds of silence to end recording
        
        self.is_recording = False
        self.temp_audio_file = Path("temp_voice_input.wav")
    
    async def capture_until_silence(self) -> str:
        """
        Record audio until user is silent for SILENCE_THRESHOLD seconds
        
        Returns:
            Transcribed text from audio
        """
        self.logger.info("Starting voice capture...")
        self.is_recording = True
        
        frames = []
        silent_frames = 0
        required_silent_frames = int(
            (self.SILENCE_THRESHOLD * self.SAMPLE_RATE) / self.CHUNK_SIZE
        )
        
        try:
            # Record audio in chunks
            with sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=1,
                blocksize=self.CHUNK_SIZE,
                dtype=np.int16
            ) as stream:
                while self.is_recording:
                    audio_chunk, _ = stream.read(self.CHUNK_SIZE)
                    
                    # Convert float to 16-bit PCM for VAD
                    audio_int16 = (audio_chunk * 32767).astype(np.int16)
                    
                    # Check for speech
                    is_speech = self.vad.is_speech(audio_int16.tobytes(), self.SAMPLE_RATE)
                    
                    if is_speech:
                        silent_frames = 0
                        self.logger.debug("Speech detected")
                    else:
                        silent_frames += 1
                        self.logger.debug(f"Silence: {silent_frames}/{required_silent_frames}")
                    
                    frames.append(audio_int16)
                    
                    # Stop if sufficient silence detected
                    if silent_frames >= required_silent_frames and len(frames) > 10:
                        self.logger.info("Silence detected, ending recording")
                        break
            
            # Save audio to file
            audio_data = np.concatenate(frames)
            wavfile.write(str(self.temp_audio_file), self.SAMPLE_RATE, audio_data)
            
            # Transcribe
            self.logger.info("Transcribing audio...")
            segments = self.model.transcribe(str(self.temp_audio_file))
            
            # Extract text
            text = ' '.join([s.text for s in segments]).strip()
            
            self.logger.info(f"Transcribed: {text}")
            
            # Cleanup
            self.temp_audio_file.unlink(missing_ok=True)
            
            return text
        
        except Exception as e:
            self.logger.error(f"Voice capture failed: {e}", exc_info=True)
            self.temp_audio_file.unlink(missing_ok=True)
            return ""
    
    def stop_recording(self):
        """Signal to stop recording (useful for timeout scenarios)"""
        self.is_recording = False
    
    async def continuous_listen(self, hotkey_handler, timeout_seconds: int = 60):
        """
        Listen for commands at intervals
        
        Args:
            hotkey_handler: Callback function(text) for recognized speech
            timeout_seconds: Maximum recording duration
        """
        while True:
            try:
                # Record audio
                text = await asyncio.wait_for(
                    self.capture_until_silence(),
                    timeout=timeout_seconds
                )
                
                if text:
                    await hotkey_handler(text)
                
                await asyncio.sleep(0.5)  # Brief pause between captures
            
            except asyncio.TimeoutError:
                self.logger.warning("Recording timeout")
            except Exception as e:
                self.logger.error(f"Listen error: {e}")
                await asyncio.sleep(1)

class VoiceCommandRouter:
    """Route voice commands to appropriate handlers"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger("VoiceRouter")
        self.voice_input = VoiceInput()
    
    async def handle_voice_input(self, text: str):
        """Process voice input through orchestrator"""
        self.logger.info(f"Voice command: {text}")
        
        # Special voice commands
        if text.lower() in ["stop", "cancel", "quit"]:
            self.voice_input.stop_recording()
            return
        
        # Route through orchestrator like keyboard input
        result = await self.orchestrator.process(text)
        
        # Optionally, generate spoken response
        if result["success"]:
            self.logger.info(f"Voice result: {result['result']}")
            # Could integrate text-to-speech here (pyttsx3)
```

### Integration with Floater UI

Add global hotkey for voice input:

```python
# In floater/main.py
import keyboard
from shared.voice_input import VoiceCommandRouter

class FloaterApp:
    def __init__(self):
        # ... existing code ...
        self.voice_router = VoiceCommandRouter(self.orchestrator)
        self._setup_hotkeys()
    
    def _setup_hotkeys(self):
        """Register global hotkeys"""
        # Ctrl+Space for voice input
        keyboard.add_hotkey('ctrl+space', self._handle_voice_hotkey)
        
        # Ctrl+Shift+I for inline input (focus input box)
        keyboard.add_hotkey('ctrl+shift+i', self._focus_input)
    
    def _handle_voice_hotkey(self):
        """Called when Ctrl+Space pressed"""
        # Optionally show recording indicator
        self.status_label.setText("🎤 Listening...")
        
        # Run async voice capture
        asyncio.create_task(self.voice_router.voice_input.capture_until_silence())
```

### Configuration

Add to `settings.json`:

```json
{
  "voice": {
    "enabled": true,
    "model_size": "base.en",
    "silence_threshold_seconds": 1.0,
    "global_hotkey": "ctrl+space",
    "use_tts_response": false,
    "tts_engine": "pyttsx3"
  }
}
```

---

## Priority 3: UI/UX - Progress Ring & Responsive Positioning

### Progress Ring Implementation

```python
# floater/widgets/progress_ring.py
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt, QRect, pyqtProperty
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from PyQt6.QtWidgets import QWidget

class ProgressRing(QWidget):
    """Animated progress ring widget"""
    
    def __init__(self, parent=None, radius: int = 50, line_width: int = 3):
        super().__init__(parent)
        
        self.radius = radius
        self.line_width = line_width
        self._progress = 0  # 0-100
        self._is_animating = False
        self._rotation = 0  # For indeterminate spinning
        
        self.setMinimumSize(radius * 2 + 10, radius * 2 + 10)
        self.setMaximumSize(radius * 2 + 10, radius * 2 + 10)
        
        # Color palette
        self.color_background = QColor("#e0e0e0")
        self.color_progress = QColor("#3498db")
        self.color_accent = QColor("#2980b9")
    
    def paintEvent(self, event):
        """Paint the progress ring"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = self.rect().center()
        
        # Draw background circle
        painter.setPen(QPen(self.color_background, self.line_width))
        painter.drawEllipse(center, self.radius, self.radius)
        
        if self._is_animating:
            # Indeterminate spinner
            painter.setPen(QPen(self.color_accent, self.line_width))
            painter.translate(center)
            painter.rotate(self._rotation)
            painter.translate(-center)
            
            # Draw arc segment
            arc_rect = QRect(
                center.x() - self.radius,
                center.y() - self.radius,
                self.radius * 2,
                self.radius * 2
            )
            painter.drawArc(arc_rect, 0 * 16, 90 * 16)
        else:
            # Determinate progress
            if self._progress > 0:
                painter.setPen(QPen(self.color_progress, self.line_width))
                arc_rect = QRect(
                    center.x() - self.radius,
                    center.y() - self.radius,
                    self.radius * 2,
                    self.radius * 2
                )
                # Start from top (90°), go counterclockwise
                span = int(self._progress * 3.6 * 16)  # Convert to 1/16 degrees
                painter.drawArc(arc_rect, 90 * 16, -span)
    
    @pyqtProperty(int)
    def progress(self) -> int:
        return self._progress
    
    @progress.setter
    def progress(self, value: int):
        self._progress = max(0, min(100, value))
        self.update()
    
    @pyqtProperty(int)
    def rotation(self) -> int:
        return self._rotation
    
    @rotation.setter
    def rotation(self, value: int):
        self._rotation = value % 360
        self.update()
    
    def start_animation(self):
        """Start indeterminate progress animation"""
        if self._is_animating:
            return
        
        self._is_animating = True
        self._progress = 0
        
        # Continuous rotation
        self._spin_timer = QTimer()
        self._spin_timer.timeout.connect(self._update_spin)
        self._spin_timer.start(50)
    
    def stop_animation(self):
        """Stop animation and show complete state"""
        if hasattr(self, '_spin_timer'):
            self._spin_timer.stop()
        
        self._is_animating = False
        self._progress = 100
        self.update()
    
    def _update_spin(self):
        """Update rotation for spinner animation"""
        self._rotation = (self._rotation + 6) % 360
        self.update()
    
    def set_progress(self, value: int):
        """Set progress percentage (0-100)"""
        self._is_animating = False
        if hasattr(self, '_spin_timer'):
            self._spin_timer.stop()
        self.progress = value

class IconWithRing(QWidget):
    """Icon with overlay progress ring"""
    
    def __init__(self, icon_pixmap, parent=None):
        super().__init__(parent)
        
        self.icon = icon_pixmap
        self.ring = ProgressRing(radius=40)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ring, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
    
    def paintEvent(self, event):
        """Paint icon in center"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = self.rect().center()
        icon_rect = self.icon.rect()
        icon_rect.moveTo(
            center.x() - icon_rect.width() // 2,
            center.y() - icon_rect.height() // 2
        )
        
        painter.drawPixmap(icon_rect, self.icon)
```

### Responsive Positioning

Replace pixel-based positioning with percentage-based layout:

```python
# floater/overlay.py - Responsive positioning
class FloaterOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.screen = QApplication.primaryScreen()
        self.position_config = {
            "x_percent": 0.03,   # 3% from left
            "y_percent": 0.16,   # 16% from top
        }
        
        self._load_position_config()
    
    def _load_position_config(self):
        """Load saved position percentage"""
        try:
            config = json.load(open("floater_position.json"))
            self.position_config.update(config)
        except FileNotFoundError:
            pass
    
    def _save_position_config(self):
        """Save position as percentage for portability"""
        config = {
            "x_percent": self.pos().x() / self.screen.geometry().width(),
            "y_percent": self.pos().y() / self.screen.geometry().height(),
        }
        with open("floater_position.json", "w") as f:
            json.dump(config, f)
    
    def _update_position(self):
        """Update position based on percentage config"""
        geometry = self.screen.geometry()
        x = int(geometry.width() * self.position_config["x_percent"])
        y = int(geometry.height() * self.position_config["y_percent"])
        self.move(x, y)
    
    def moveEvent(self, event):
        """Track position changes"""
        super().moveEvent(event)
        self._save_position_config()
    
    def resizeScreen(self):
        """Called when screen resolution changes"""
        self._update_position()
```

### Control Buttons Overlay

Add buttons directly on icon for quick actions:

```python
# floater/widgets/icon_controls.py
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class IconControlButton(QPushButton):
    """Small control button overlaid on icon"""
    
    def __init__(self, icon_char: str = "⚙", size: int = 24, parent=None):
        super().__init__(icon_char, parent)
        
        self.setFixedSize(size, size)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(52, 152, 219, 0.9);
                color: white;
                border: none;
                border-radius: {size // 2}px;
                font-weight: bold;
                font-size: {size - 4}px;
            }}
            QPushButton:hover {{
                background-color: rgba(41, 128, 185, 1.0);
            }}
            QPushButton:pressed {{
                background-color: rgba(30, 90, 130, 1.0);
            }}
        """)

class FloaterIconWithControls(QWidget):
    """Icon with control buttons positioned around it"""
    
    settings_clicked = pyqtSignal()
    voice_clicked = pyqtSignal()
    
    def __init__(self, icon_pixmap, parent=None):
        super().__init__(parent)
        
        self.icon_size = 80
        self.setFixedSize(140, 140)
        
        # Central icon
        self.icon_label = QLabel()
        self.icon_label.setPixmap(icon_pixmap.scaled(
            self.icon_size, self.icon_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        
        # Control buttons
        self.btn_settings = IconControlButton("⚙", size=28)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        
        self.btn_voice = IconControlButton("🎤", size=28)
        self.btn_voice.clicked.connect(self.voice_clicked.emit)
        
        # Layout with buttons positioned around icon
        self._layout_controls()
    
    def _layout_controls(self):
        """Position buttons around central icon"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top row: settings button centered at top
        top_row = QHBoxLayout()
        top_row.addStretch()
        top_row.addWidget(self.btn_settings)
        top_row.addStretch()
        
        # Middle row: icon centered
        middle_row = QHBoxLayout()
        middle_row.addStretch()
        middle_row.addWidget(self.icon_label)
        middle_row.addStretch()
        
        # Bottom row: voice button centered at bottom
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        bottom_row.addWidget(self.btn_voice)
        bottom_row.addStretch()
        
        layout.addLayout(top_row)
        layout.addLayout(middle_row)
        layout.addLayout(bottom_row)
        
        self.setLayout(layout)
```

---

## Priority 4: Local LLM Strategy - Optimal Configuration

### Model Selection for 12GB VRAM

**Primary Model**: `qwen2.5:7b` (Recommended)
- **VRAM**: 6-7GB at Q4 quantization
- **Strengths**: Excellent instruction following, JSON parsing, code understanding
- **Speed**: ~50 tokens/sec on your hardware
- **Use cases**: Intent classification, command parsing, summarization

**Fallback Model**: `phi-3.5:3.8b`
- **VRAM**: 3-4GB at Q4
- **Strengths**: Very fast, lightweight, good for quick responses
- **Speed**: ~80 tokens/sec
- **Use cases**: Quick clarifications, error messages, when Qwen is busy

**Vision Model**: `moondream2` (Not LLaVA)
- **VRAM**: 2.5-3GB at FP16
- **Strengths**: Explicitly designed for resource-constrained environments
- **Use case**: Screenshot analysis, coordinate extraction for vision agent

### Configuration & Model Loading Strategy

```python
# shared/llm_manager.py
import ollama
import asyncio
import logging
from typing import Optional

class LLMManager:
    """Intelligent LLM model loading and switching"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.client = ollama.Client(self.ollama_url)
        self.logger = logging.getLogger("LLMManager")
        
        self.current_model = None
        self.loaded_models = set()
        
        # Model configurations
        self.models = {
            "qwen2.5:7b": {
                "vram_gb": 7,
                "speed_tps": 50,
                "primary": True,
                "use_cases": ["classify", "parse", "summarize"]
            },
            "phi-3.5:3.8b": {
                "vram_gb": 4,
                "speed_tps": 80,
                "primary": False,
                "use_cases": ["quick_response", "clarify"]
            },
            "moondream2": {
                "vram_gb": 3,
                "vision": True,
                "use_cases": ["image_analysis", "coordinates"]
            }
        }
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        use_case: str = "general"
    ) -> str:
        """
        Generate response, automatically selecting/loading best model
        
        Args:
            prompt: User prompt
            model: Specific model to use (optional)
            use_case: Type of task (for automatic model selection)
        
        Returns:
            Generated text
        """
        
        # Select model if not specified
        if not model:
            model = self._select_model_for_use_case(use_case)
        
        # Ensure model is loaded
        await self._ensure_model_loaded(model)
        
        try:
            self.logger.info(f"Generating with {model}: {prompt[:50]}...")
            
            response = await asyncio.to_thread(
                self.client.generate,
                model=model,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": 0.1,  # Low for deterministic output
                    "top_p": 0.9,
                    "top_k": 40,
                }
            )
            
            return response["response"]
        
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            raise
    
    def _select_model_for_use_case(self, use_case: str) -> str:
        """Select best model for task type"""
        
        # Use case priority mapping
        use_case_priority = {
            "classify": "qwen2.5:7b",      # High quality needed
            "parse": "qwen2.5:7b",          # JSON accuracy critical
            "summarize": "qwen2.5:7b",      # Needs comprehension
            "quick_response": "phi-3.5:3.8b",
            "clarify": "phi-3.5:3.8b",
            "image_analysis": "moondream2",
            "coordinates": "moondream2",
        }
        
        return use_case_priority.get(use_case, "qwen2.5:7b")
    
    async def _ensure_model_loaded(self, model: str):
        """Load model if not already loaded"""
        
        if model in self.loaded_models:
            self.logger.debug(f"{model} already loaded")
            return
        
        # Unload other models if loading a new one
        # (Optional: only keep primary model loaded)
        if self.current_model and self.current_model != model:
            self.logger.info(f"Unloading {self.current_model}...")
            await self._unload_model(self.current_model)
        
        self.logger.info(f"Loading {model}...")
        
        try:
            # Trigger model load by calling with dummy prompt
            await asyncio.to_thread(
                self.client.generate,
                model=model,
                prompt="hi",
                stream=False
            )
            
            self.loaded_models.add(model)
            self.current_model = model
            self.logger.info(f"{model} loaded successfully")
        
        except Exception as e:
            self.logger.error(f"Failed to load {model}: {e}")
            raise
    
    async def _unload_model(self, model: str):
        """Unload model from memory"""
        try:
            # Send empty context to unload
            self.client.generate(model=model, prompt="", keep_alive=0)
            self.loaded_models.discard(model)
        except:
            pass
    
    async def batch_generate(self, prompts: list, model: str = "qwen2.5:7b") -> list:
        """Generate multiple responses efficiently"""
        results = []
        for prompt in prompts:
            result = await self.generate(prompt, model=model)
            results.append(result)
        return results
    
    def get_loaded_models(self) -> list:
        """Get currently loaded models"""
        return list(self.loaded_models)
    
    def get_model_info(self, model: str) -> dict:
        """Get model configuration"""
        return self.models.get(model, {})
```

### Integration with Orchestrator

```python
# In shared/orchestrator.py - Add LLM integration
from shared.llm_manager import LLMManager

class Orchestrator:
    def __init__(self, config: Dict):
        # ... existing code ...
        self.llm = LLMManager(config.get("ollama_url"))
    
    async def classifier.classify_with_llm(self, user_input: str) -> Command:
        """Use LLM for complex classification"""
        
        prompt = f"""Parse this user command. Return ONLY valid JSON.

User: "{user_input}"

Respond with JSON: {{"agent": "...", "action": "...", "params": {{}}}}
JSON:"""
        
        # Use LLM manager for intelligent model selection
        response = await self.llm.generate(
            prompt,
            use_case="parse"  # Automatically selects best model
        )
        
        # Parse response...
```

---

## Priority 5: Y-IT Monetization - Production Integration

### Revenue Model

**Target**: $1,500/month survival = 10 gurus at $150/month

**Workflow**:
1. User specifies target guru (e.g., "Joe Rogan")
2. hndl-it automatically:
   - Scrapes primary sites (blog, podcast archives)
   - Extracts claims via vision + text parsing
   - Deduplicates across sources
   - Generates comparison JSON
   - Email delivery of updated analysis

### Implementation

```python
# y-it/pipeline.py
from shared.orchestrator import get_orchestrator
from shared.llm_manager import LLMManager
from pathlib import Path
import json
import asyncio

class YITPipeline:
    """Automated Y-IT research pipeline"""
    
    def __init__(self, orchestrator=None, llm=None):
        self.orchestrator = orchestrator or get_orchestrator()
        self.llm = llm or LLMManager()
        self.logger = logging.getLogger("YITPipeline")
    
    async def research_guru(self, guru_name: str, sites: list = None) -> dict:
        """
        Complete research workflow for target guru
        
        Args:
            guru_name: Name of guru to research (e.g., "Andrew Tate")
            sites: List of URLs to scrape (optional)
        
        Returns:
            Dictionary with claims, sources, timestamps
        """
        
        if not sites:
            sites = await self._get_default_sites(guru_name)
        
        self.logger.info(f"Starting research: {guru_name}")
        
        # Phase 1: Scrape all sites
        self.logger.info("Phase 1: Scraping...")
        claims_by_site = {}
        
        for url in sites:
            try:
                claims = await self._scrape_site(guru_name, url)
                claims_by_site[url] = claims
                self.logger.info(f"  ✓ {url}: {len(claims)} claims")
            except Exception as e:
                self.logger.error(f"  ✗ {url}: {e}")
        
        # Phase 2: Extract from images (vision)
        self.logger.info("Phase 2: Vision extraction...")
        image_claims = await self._extract_from_images(guru_name)
        self.logger.info(f"  ✓ Extracted {len(image_claims)} image-based claims")
        
        # Phase 3: Deduplicate & normalize
        self.logger.info("Phase 3: Deduplication...")
        all_claims = [c for claims in claims_by_site.values() for c in claims] + image_claims
        unique_claims = await self._deduplicate_claims(all_claims)
        self.logger.info(f"  ✓ {len(all_claims)} → {len(unique_claims)} unique")
        
        # Phase 4: Generate analysis
        self.logger.info("Phase 4: Analysis...")
        analysis = await self._generate_analysis(guru_name, unique_claims)
        
        # Phase 5: Save to cloud
        self.logger.info("Phase 5: Saving...")
        output = {
            "guru": guru_name,
            "date": datetime.now().isoformat(),
            "sources": list(claims_by_site.keys()),
            "claim_count": len(unique_claims),
            "claims": unique_claims,
            "analysis": analysis
        }
        
        await self._save_to_cloud(guru_name, output)
        
        self.logger.info(f"✓ Research complete: {guru_name}")
        return output
    
    async def _scrape_site(self, guru_name: str, url: str) -> list:
        """Scrape website for guru claims"""
        
        command = f'go to "{url}", find all mentions of "{guru_name}", scrape to JSON'
        result = await self.orchestrator.process(command)
        
        if result["success"]:
            try:
                data = json.loads(result["result"])
                return data.get("claims", [])
            except:
                return []
        return []
    
    async def _extract_from_images(self, guru_name: str) -> list:
        """Extract claims from screenshots using vision"""
        
        # Get list of local screenshots
        result = await self.orchestrator.process(
            "list ~/Downloads, show all .png and .jpg files from last week"
        )
        
        claims = []
        
        # For each image, ask vision agent to extract text about guru
        for image_file in result.get("files", []):
            try:
                extraction = await self.orchestrator.process(
                    f'extract text mentioning "{guru_name}" from {image_file}'
                )
                
                if extraction["success"]:
                    claims.append({
                        "text": extraction["result"],
                        "source": "image",
                        "file": image_file
                    })
            except Exception as e:
                self.logger.debug(f"Image extraction failed: {e}")
        
        return claims
    
    async def _deduplicate_claims(self, claims: list) -> list:
        """Remove duplicate claims using LLM"""
        
        if not claims:
            return []
        
        # Group similar claims
        prompt = f"""Deduplicate these {len(claims)} claims about a guru.
Remove exact duplicates and near-duplicates.
Return JSON array of unique claims only.

Claims:
{json.dumps(claims, indent=2)}

Unique claims (JSON array):"""
        
        response = await self.llm.generate(prompt, use_case="summarize")
        
        try:
            unique = json.loads(response)
            return unique
        except:
            return claims
    
    async def _generate_analysis(self, guru_name: str, claims: list) -> dict:
        """Generate analytical summary"""
        
        prompt = f"""Analyze these {len(claims)} claims about {guru_name}.

Categorize into:
- Provable: Claims that can be factually verified
- Disputed: Claims contradicted by evidence
- Unverifiable: Claims without testable claims
- Opinion: Claims that are subjective

Format as JSON.

Claims:
{json.dumps(claims[:20], indent=2)}

Analysis:"""
        
        response = await self.llm.generate(prompt, use_case="summarize")
        
        try:
            return json.loads(response)
        except:
            return {"error": "Analysis generation failed"}
    
    async def _save_to_cloud(self, guru_name: str, output: dict):
        """Save result to Google Drive"""
        
        # Save locally first
        local_path = Path(f"research/{guru_name}_{datetime.now().date()}.json")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(local_path, "w") as f:
            json.dump(output, f, indent=2)
        
        # Upload to cloud via desktop agent
        await self.orchestrator.process(
            f'upload "{local_path}" to "Y-IT Research" Google Drive folder'
        )
    
    async def _get_default_sites(self, guru_name: str) -> list:
        """Get default scraping targets"""
        
        # This would be configured per guru
        default_sites = {
            "andrew tate": [
                "https://www.andrewtatewatches.com",
                "https://www.hustlersuniversity.com/blog",
                # More sites...
            ],
            # Add more gurus...
        }
        
        return default_sites.get(guru_name.lower(), [])

# Scheduled execution
async def scheduled_research():
    """Run research updates on schedule"""
    pipeline = YITPipeline()
    
    # Get list of active gurus from config
    with open("y-it/gurus.json") as f:
        gurus = json.load(f)
    
    for guru in gurus:
        try:
            await pipeline.research_guru(guru["name"])
            await asyncio.sleep(60)  # Avoid rate limiting
        except Exception as e:
            logging.error(f"Research failed for {guru['name']}: {e}")
```

### Configuration File

```json
// y-it/gurus.json
[
  {
    "name": "Andrew Tate",
    "tier": "premium",
    "sites": ["...", "..."],
    "update_frequency": "weekly",
    "email_delivery": true,
    "subscriber_count": 3
  },
  {
    "name": "Joe Rogan",
    "tier": "premium",
    "sites": ["...", "..."],
    "update_frequency": "weekly",
    "email_delivery": true,
    "subscriber_count": 7
  }
]
```

---

## Priority 6: Error Handling & Resilience

### Timeouts & Retries

```python
# shared/resilience.py
import asyncio
from typing import Callable, Any

async def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0
) -> Any:
    """Retry function with exponential backoff"""
    
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            delay = min(base_delay * (2 ** attempt), max_delay)
            logging.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
            await asyncio.sleep(delay)

async def timeout_handler(
    coro,
    timeout_seconds: float,
    fallback_response: str = "Operation timed out"
) -> str:
    """Handle operation timeouts gracefully"""
    
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logging.warning(f"Operation timed out after {timeout_seconds}s")
        return fallback_response
```

---

## Questions for Clarification

1. **Voice input priority**: Should voice be available globally (anywhere on Windows) or only when hndl-it floater is visible?

2. **Model loading strategy**: Keep Qwen loaded permanently, or load on-demand? (Affects startup time vs VRAM availability)

3. **Y-IT MVP scope**: Start with 1 guru (prove workflow) or 3 gurus (demonstrate scale)?

4. **Cloud storage**: Google Drive integration essential, or can you start with local storage?

5. **Authentication**: Plan for multi-user accounts, or single-user personal tool initially?

---

## Implementation Roadmap (Next 6 Weeks)

| Week | Priority | Tasks | Hrs |
|------|----------|-------|-----|
| **1** | 1-2 | Orchestrator + Voice input | 18 |
| **2** | 2-3 | LLM integration + Progress ring | 14 |
| **3** | 3-4 | Responsive UI + Memory system | 12 |
| **4** | 5 | Y-IT Pipeline (1 guru) | 16 |
| **5** | 5 | Y-IT Scale (3 gurus) + Testing | 14 |
| **6** | 6 | Documentation + Deployment | 10 |
| **Total** | | | **84 hours** |

---

## Success Metrics

After 6 weeks, you should have:

✅ End-to-end command routing (floater → orchestrator → agent → response)
✅ Voice input working with Ctrl+Space hotkey
✅ Local LLM handling 80%+ of intent classification
✅ 3 gurus with weekly automated research
✅ Progress indication on UI
✅ Complete execution history for debugging

**Revenue**: First paying customer for 1 guru = proof of concept ✓

---

## Bottom Line

Your project is architecturally sound. The work ahead is **integration and optimization**, not redesign. The orchestrator is your critical path—once it exists, everything else (voice, vision, Y-IT) integrates smoothly. The Y-IT pipeline is both your immediate revenue stream and best way to validate the system works end-to-end.

Priority sequence: **Orchestrator → Voice → Y-IT Pipeline**

Everything else is polish that can happen in parallel.

---

*Generated by Perplexity (Sonic) on 2026-01-10*
*For: hndl-it project ecosystem*
