class AudioWaveformVisualizer {
    constructor() {
        this.audioContext = null;
        this.microphone = null;
        this.analyser = null;
        this.oscillator = null;
        this.gainNode = null;
        this.outputGainNode = null;
        this.isRecording = false;
        this.isPlayingTone = false;
        this.animationId = null;
        this.outputAnimationId = null;
        
        // Canvas elements
        this.waveformCanvas = document.getElementById('waveformCanvas');
        this.waveformCtx = this.waveformCanvas.getContext('2d');
        this.outputCanvas = document.getElementById('outputCanvas');
        this.outputCtx = this.outputCanvas.getContext('2d');
        
        // Control elements
        this.microphoneSelect = document.getElementById('microphoneSelect');
        this.speakerSelect = document.getElementById('speakerSelect');
        this.startButton = document.getElementById('startRecording');
        this.stopButton = document.getElementById('stopRecording');
        this.playToneButton = document.getElementById('playTone');
        this.stopToneButton = document.getElementById('stopTone');
        this.micVolumeSlider = document.getElementById('micVolume');
        this.outputVolumeSlider = document.getElementById('outputVolume');
        this.frequencySlider = document.getElementById('frequency');
        
        // Volume display elements
        this.micVolumeValue = document.getElementById('micVolumeValue');
        this.outputVolumeValue = document.getElementById('outputVolumeValue');
        this.frequencyValue = document.getElementById('frequencyValue');
        
        // Waveform data
        this.dataArray = null;
        this.bufferLength = 0;
        this.outputDataArray = null;
        this.outputBufferLength = 0;
        
        this.init();
    }
    
    async init() {
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize audio context
        await this.initAudioContext();
        
        // Get available devices
        await this.getAudioDevices();
        
        // Setup canvas
        this.setupCanvas();
    }
    
    setupEventListeners() {
        this.startButton.addEventListener('click', () => this.startRecording());
        this.stopButton.addEventListener('click', () => this.stopRecording());
        this.playToneButton.addEventListener('click', () => this.playTone());
        this.stopToneButton.addEventListener('click', () => this.stopTone());
        
        // Volume controls
        this.micVolumeSlider.addEventListener('input', (e) => {
            this.micVolumeValue.textContent = e.target.value;
            this.updateMicrophoneGain();
        });
        
        this.outputVolumeSlider.addEventListener('input', (e) => {
            this.outputVolumeValue.textContent = e.target.value;
            this.updateOutputVolume();
        });
        
        this.frequencySlider.addEventListener('input', (e) => {
            this.frequencyValue.textContent = e.target.value;
            this.updateFrequency();
        });
        
        // Device selection
        this.speakerSelect.addEventListener('change', () => this.changeOutputDevice());
    }
    
    async initAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Resume audio context if suspended
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }
        } catch (error) {
            console.error('Error initializing audio context:', error);
            alert('Error initializing audio. Please check your browser permissions.');
        }
    }
    
    async getAudioDevices() {
        try {
            // Request microphone permission first
            await navigator.mediaDevices.getUserMedia({ audio: true });
            
            const devices = await navigator.mediaDevices.enumerateDevices();
            
            // Clear existing options
            this.microphoneSelect.innerHTML = '<option value="">Select Microphone</option>';
            this.speakerSelect.innerHTML = '<option value="">Default Speaker</option>';
            
            devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.textContent = device.label || `${device.kind} ${device.deviceId.substring(0, 8)}...`;
                
                if (device.kind === 'audioinput') {
                    this.microphoneSelect.appendChild(option);
                } else if (device.kind === 'audiooutput') {
                    this.speakerSelect.appendChild(option);
                }
            });
        } catch (error) {
            console.error('Error getting audio devices:', error);
            alert('Error accessing audio devices. Please grant microphone permissions.');
        }
    }
    
    setupCanvas() {
        // Set canvas resolution
        const dpr = window.devicePixelRatio || 1;
        const rect = this.waveformCanvas.getBoundingClientRect();
        
        this.waveformCanvas.width = rect.width * dpr;
        this.waveformCanvas.height = rect.height * dpr;
        this.waveformCtx.scale(dpr, dpr);
        
        this.outputCanvas.width = rect.width * dpr;
        this.outputCanvas.height = rect.height * dpr;
        this.outputCtx.scale(dpr, dpr);
        
        // Draw initial state
        this.drawWaveform(this.waveformCtx, null, 'Microphone Input');
        this.drawWaveform(this.outputCtx, null, 'Audio Output');
    }
    
    async startRecording() {
        try {
            const deviceId = this.microphoneSelect.value;
            const constraints = {
                audio: {
                    deviceId: deviceId ? { exact: deviceId } : undefined,
                    echoCancellation: false,
                    noiseSuppression: false,
                    autoGainControl: false
                }
            };
            
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            
            // Create audio nodes
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            this.analyser = this.audioContext.createAnalyser();
            this.gainNode = this.audioContext.createGain();
            
            // Configure analyser
            this.analyser.fftSize = 2048;
            this.bufferLength = this.analyser.frequencyBinCount;
            this.dataArray = new Uint8Array(this.bufferLength);
            
            // Connect nodes
            this.microphone.connect(this.gainNode);
            this.gainNode.connect(this.analyser);
            
            // Update gain
            this.updateMicrophoneGain();
            
            // Start visualization
            this.isRecording = true;
            this.visualizeMicrophone();
            
            // Update UI
            this.startButton.disabled = true;
            this.stopButton.disabled = false;
            
        } catch (error) {
            console.error('Error starting recording:', error);
            alert('Error starting microphone recording. Please check permissions and device selection.');
        }
    }
    
    stopRecording() {
        this.isRecording = false;
        
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.microphone) {
            this.microphone.disconnect();
            this.microphone = null;
        }
        
        if (this.analyser) {
            this.analyser.disconnect();
            this.analyser = null;
        }
        
        if (this.gainNode) {
            this.gainNode.disconnect();
            this.gainNode = null;
        }
        
        // Clear canvas
        this.drawWaveform(this.waveformCtx, null, 'Microphone Input (Stopped)');
        
        // Update UI
        this.startButton.disabled = false;
        this.stopButton.disabled = true;
    }
    
    async playTone() {
        try {
            this.oscillator = this.audioContext.createOscillator();
            this.outputGainNode = this.audioContext.createGain();
            const outputAnalyser = this.audioContext.createAnalyser();
            
            // Configure oscillator
            this.oscillator.type = 'sine';
            this.oscillator.frequency.setValueAtTime(
                parseFloat(this.frequencySlider.value), 
                this.audioContext.currentTime
            );
            
            // Configure analyser for output visualization
            outputAnalyser.fftSize = 2048;
            this.outputBufferLength = outputAnalyser.frequencyBinCount;
            this.outputDataArray = new Uint8Array(this.outputBufferLength);
            
            // Connect nodes
            this.oscillator.connect(this.outputGainNode);
            this.outputGainNode.connect(outputAnalyser);
            this.outputGainNode.connect(this.audioContext.destination);
            
            // Set volume
            this.updateOutputVolume();
            
            // Start oscillator
            this.oscillator.start();
            this.isPlayingTone = true;
            
            // Start visualization
            this.visualizeOutput(outputAnalyser);
            
            // Handle oscillator end
            this.oscillator.onended = () => {
                this.stopTone();
            };
            
            // Update UI
            this.playToneButton.disabled = true;
            this.stopToneButton.disabled = false;
            
        } catch (error) {
            console.error('Error playing tone:', error);
            alert('Error playing audio tone.');
        }
    }
    
    stopTone() {
        this.isPlayingTone = false;
        
        if (this.outputAnimationId) {
            cancelAnimationFrame(this.outputAnimationId);
        }
        
        if (this.oscillator) {
            this.oscillator.stop();
            this.oscillator.disconnect();
            this.oscillator = null;
        }
        
        if (this.outputGainNode) {
            this.outputGainNode.disconnect();
            this.outputGainNode = null;
        }
        
        // Clear canvas
        this.drawWaveform(this.outputCtx, null, 'Audio Output (Stopped)');
        
        // Update UI
        this.playToneButton.disabled = false;
        this.stopToneButton.disabled = true;
    }
    
    updateMicrophoneGain() {
        if (this.gainNode) {
            const volume = parseFloat(this.micVolumeSlider.value) / 50; // 0-2 range
            this.gainNode.gain.setValueAtTime(volume, this.audioContext.currentTime);
        }
    }
    
    updateOutputVolume() {
        if (this.outputGainNode) {
            const volume = parseFloat(this.outputVolumeSlider.value) / 100; // 0-1 range
            this.outputGainNode.gain.setValueAtTime(volume, this.audioContext.currentTime);
        }
    }
    
    updateFrequency() {
        if (this.oscillator) {
            const frequency = parseFloat(this.frequencySlider.value);
            this.oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
        }
    }
    
    async changeOutputDevice() {
        const deviceId = this.speakerSelect.value;
        if (deviceId && this.audioContext.setSinkId) {
            try {
                await this.audioContext.setSinkId(deviceId);
            } catch (error) {
                console.error('Error changing output device:', error);
                alert('Error changing output device. This feature may not be supported in your browser.');
            }
        }
    }
    
    visualizeMicrophone() {
        if (!this.isRecording) return;
        
        this.analyser.getByteTimeDomainData(this.dataArray);
        this.drawWaveform(this.waveformCtx, this.dataArray, 'Microphone Input (Live)');
        
        this.animationId = requestAnimationFrame(() => this.visualizeMicrophone());
    }
    
    visualizeOutput(analyser) {
        if (!this.isPlayingTone) return;
        
        analyser.getByteTimeDomainData(this.outputDataArray);
        this.drawWaveform(this.outputCtx, this.outputDataArray, 'Audio Output (Live)');
        
        this.outputAnimationId = requestAnimationFrame(() => this.visualizeOutput(analyser));
    }
    
    drawWaveform(ctx, dataArray, title) {
        const canvas = ctx.canvas;
        const width = canvas.width / (window.devicePixelRatio || 1);
        const height = canvas.height / (window.devicePixelRatio || 1);
        
        // Clear canvas
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, width, height);
        
        // Draw grid
        ctx.strokeStyle = '#e9ecef';
        ctx.lineWidth = 0.5;
        
        // Horizontal lines
        for (let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        
        // Vertical lines
        for (let i = 0; i <= 8; i++) {
            const x = (width / 8) * i;
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }
        
        // Draw center line
        ctx.strokeStyle = '#6c757d';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.stroke();
        
        if (dataArray) {
            // Draw waveform
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#667eea';
            ctx.beginPath();
            
            const sliceWidth = width / dataArray.length;
            let x = 0;
            
            for (let i = 0; i < dataArray.length; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * height / 2;
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
                
                x += sliceWidth;
            }
            
            ctx.stroke();
            
            // Draw RMS level indicator
            const rms = this.calculateRMS(dataArray);
            const rmsHeight = (rms / 128.0) * height;
            
            ctx.fillStyle = 'rgba(102, 126, 234, 0.3)';
            ctx.fillRect(width - 20, height - rmsHeight, 10, rmsHeight);
            
            // RMS text
            ctx.fillStyle = '#495057';
            ctx.font = '12px Arial';
            ctx.fillText(`RMS: ${Math.round(rms)}`, width - 60, height - 10);
        }
        
        // Draw title
        ctx.fillStyle = '#495057';
        ctx.font = 'bold 14px Arial';
        ctx.fillText(title, 10, 20);
        
        // Draw no signal message if no data
        if (!dataArray) {
            ctx.fillStyle = '#6c757d';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No Signal', width / 2, height / 2);
            ctx.textAlign = 'left';
        }
    }
    
    calculateRMS(dataArray) {
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            const sample = (dataArray[i] - 128) / 128.0;
            sum += sample * sample;
        }
        return Math.sqrt(sum / dataArray.length) * 128;
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Check for Web Audio API support
    if (!window.AudioContext && !window.webkitAudioContext) {
        alert('Your browser does not support the Web Audio API. Please use a modern browser.');
        return;
    }
    
    // Check for getUserMedia support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Your browser does not support microphone access. Please use a modern browser.');
        return;
    }
    
    // Initialize the visualizer
    new AudioWaveformVisualizer();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, could pause audio processing if needed
        console.log('Page hidden');
    } else {
        // Page is visible again
        console.log('Page visible');
    }
});
