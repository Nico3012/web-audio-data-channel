package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"net/http"
	"sync"
	"time"

	"github.com/gordonklaus/portaudio"
	"github.com/gorilla/mux"
)

const (
	sampleRate      = 44100
	framesPerBuffer = 1024
	channels        = 1
)

type AudioVisualizer struct {
	stream         *portaudio.Stream
	outputStream   *portaudio.Stream
	audioBuffer    []float32
	fftData        []float64
	isRecording    bool
	isPlaying      bool
	mu             sync.RWMutex
	outputBuffer   []float32
	frequency      float64
	amplitude      float64
	phase          float64 // For sine wave continuity
	latestAmpData  []float64
	latestFreqData []float64
	dataTimestamp  int64
}

type DeviceInfo struct {
	Index      int    `json:"index"`
	Name       string `json:"name"`
	DeviceType string `json:"deviceType"` // "input" or "output"
	Channels   int    `json:"channels"`
}

type VisualizationData struct {
	Type      string    `json:"type"`
	Timestamp int64     `json:"timestamp"`
	Amplitude []float64 `json:"amplitude,omitempty"`
	Frequency []float64 `json:"frequency,omitempty"`
}

func NewAudioVisualizer() *AudioVisualizer {
	return &AudioVisualizer{
		audioBuffer:    make([]float32, framesPerBuffer),
		outputBuffer:   make([]float32, framesPerBuffer),
		fftData:        make([]float64, framesPerBuffer/2),
		frequency:      440.0, // Default frequency (A4)
		amplitude:      0.3,   // Default amplitude
		latestAmpData:  make([]float64, framesPerBuffer),
		latestFreqData: make([]float64, framesPerBuffer/2),
	}
}

func (av *AudioVisualizer) initPortAudio() error {
	return portaudio.Initialize()
}

func (av *AudioVisualizer) terminate() {
	portaudio.Terminate()
}

func (av *AudioVisualizer) getAudioDevices() ([]DeviceInfo, error) {
	devices, err := portaudio.Devices()
	if err != nil {
		return nil, err
	}

	var allDevices []DeviceInfo
	for i, device := range devices {
		if device.MaxInputChannels > 0 {
			allDevices = append(allDevices, DeviceInfo{
				Index:      i,
				Name:       device.Name,
				DeviceType: "input",
				Channels:   device.MaxInputChannels,
			})
		}
		if device.MaxOutputChannels > 0 {
			allDevices = append(allDevices, DeviceInfo{
				Index:      i,
				Name:       device.Name,
				DeviceType: "output",
				Channels:   device.MaxOutputChannels,
			})
		}
	}
	return allDevices, nil
}

func (av *AudioVisualizer) startRecording(deviceIndex int) error {
	av.mu.Lock()
	defer av.mu.Unlock()

	if av.isRecording {
		av.stream.Stop()
		av.stream.Close()
	}

	devices, err := portaudio.Devices()
	if err != nil {
		return err
	}

	if deviceIndex < 0 || deviceIndex >= len(devices) {
		return fmt.Errorf("invalid device index: %d", deviceIndex)
	}

	inputDevice := devices[deviceIndex]

	streamParms := portaudio.StreamParameters{
		Input: portaudio.StreamDeviceParameters{
			Device:   inputDevice,
			Channels: channels,
			Latency:  inputDevice.DefaultLowInputLatency,
		},
		SampleRate:      sampleRate,
		FramesPerBuffer: framesPerBuffer,
	}

	stream, err := portaudio.OpenStream(streamParms, av.audioCallback)
	if err != nil {
		return err
	}

	av.stream = stream
	err = stream.Start()
	if err != nil {
		return err
	}

	av.isRecording = true
	log.Printf("Started recording from device: %s", inputDevice.Name)
	return nil
}

func (av *AudioVisualizer) stopRecording() error {
	av.mu.Lock()
	defer av.mu.Unlock()

	if !av.isRecording {
		return nil
	}

	err := av.stream.Stop()
	if err != nil {
		return err
	}

	err = av.stream.Close()
	if err != nil {
		return err
	}

	av.isRecording = false
	log.Println("Stopped recording")
	return nil
}

func (av *AudioVisualizer) startPlayback(deviceIndex int, frequency, amplitude float64) error {
	av.mu.Lock()
	defer av.mu.Unlock()

	if av.isPlaying {
		av.outputStream.Stop()
		av.outputStream.Close()
	}

	devices, err := portaudio.Devices()
	if err != nil {
		return err
	}

	if deviceIndex < 0 || deviceIndex >= len(devices) {
		return fmt.Errorf("invalid output device index: %d", deviceIndex)
	}

	outputDevice := devices[deviceIndex]
	if outputDevice.MaxOutputChannels == 0 {
		return fmt.Errorf("device %s has no output channels", outputDevice.Name)
	}

	av.frequency = frequency
	av.amplitude = amplitude

	streamParms := portaudio.StreamParameters{
		Output: portaudio.StreamDeviceParameters{
			Device:   outputDevice,
			Channels: channels,
			Latency:  outputDevice.DefaultLowOutputLatency,
		},
		SampleRate:      sampleRate,
		FramesPerBuffer: framesPerBuffer,
	}

	stream, err := portaudio.OpenStream(streamParms, av.outputCallback)
	if err != nil {
		return err
	}

	av.outputStream = stream
	err = stream.Start()
	if err != nil {
		return err
	}

	av.isPlaying = true
	log.Printf("Started playback on device: %s at %.1fHz", outputDevice.Name, frequency)
	return nil
}

func (av *AudioVisualizer) stopPlayback() error {
	av.mu.Lock()
	defer av.mu.Unlock()

	if !av.isPlaying {
		return nil
	}

	err := av.outputStream.Stop()
	if err != nil {
		return err
	}

	err = av.outputStream.Close()
	if err != nil {
		return err
	}

	av.isPlaying = false
	log.Println("Stopped playback")
	return nil
}

func (av *AudioVisualizer) outputCallback(outputBuffer []float32) {
	av.mu.Lock()
	frequency := av.frequency
	amplitude := av.amplitude
	phase := av.phase
	av.mu.Unlock()

	// Generate sine wave with phase continuity
	for i := range outputBuffer {
		// Generate sine wave: amplitude * sin(phase)
		sample := amplitude * math.Sin(phase)
		outputBuffer[i] = float32(sample)

		// Update phase for next sample
		phase += 2 * math.Pi * frequency / sampleRate
	}

	// Keep phase in reasonable range to avoid floating point issues
	for phase > 2*math.Pi {
		phase -= 2 * math.Pi
	}

	av.mu.Lock()
	av.phase = phase
	av.mu.Unlock()
}

func (av *AudioVisualizer) audioCallback(inputBuffer []float32) {
	av.mu.Lock()
	copy(av.audioBuffer, inputBuffer)
	av.mu.Unlock()

	// Process audio for visualization
	av.processAudioData(inputBuffer)
}

func (av *AudioVisualizer) processAudioData(buffer []float32) {
	av.mu.Lock()
	defer av.mu.Unlock()

	// Calculate amplitude data for waveform visualization
	for i, sample := range buffer {
		if i < len(av.latestAmpData) {
			av.latestAmpData[i] = float64(sample)
		}
	}

	// Simple FFT approximation for frequency visualization
	frequencyData := av.calculateFFT(buffer)
	copy(av.latestFreqData, frequencyData)

	// Update timestamp
	av.dataTimestamp = time.Now().UnixMilli()
}

func (av *AudioVisualizer) calculateFFT(buffer []float32) []float64 {
	// Simple magnitude calculation for frequency bins
	// This is a simplified approach - for real FFT, consider using a proper FFT library
	n := len(buffer) / 2
	result := make([]float64, n)

	for i := 0; i < n; i++ {
		// Calculate magnitude for frequency bin
		real := float64(buffer[i])
		imag := float64(buffer[i+n/2])
		magnitude := math.Sqrt(real*real + imag*imag)
		result[i] = magnitude
	}

	return result
}

func (av *AudioVisualizer) handleAudioData(w http.ResponseWriter, r *http.Request) {
	av.mu.RLock()
	defer av.mu.RUnlock()

	if !av.isRecording {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"recording": false,
		})
		return
	}

	// Return both amplitude and frequency data
	data := map[string]interface{}{
		"recording": true,
		"timestamp": av.dataTimestamp,
		"amplitude": av.latestAmpData,
		"frequency": av.latestFreqData,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

func (av *AudioVisualizer) handleDevices(w http.ResponseWriter, r *http.Request) {
	devices, err := av.getAudioDevices()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(devices)
}

func (av *AudioVisualizer) handleStartRecording(w http.ResponseWriter, r *http.Request) {
	var request struct {
		DeviceIndex int `json:"deviceIndex"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	if err := av.startRecording(request.DeviceIndex); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "recording started"})
}

func (av *AudioVisualizer) handleStopRecording(w http.ResponseWriter, r *http.Request) {
	if err := av.stopRecording(); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "recording stopped"})
}

func (av *AudioVisualizer) handleStartPlayback(w http.ResponseWriter, r *http.Request) {
	var request struct {
		DeviceIndex int     `json:"deviceIndex"`
		Frequency   float64 `json:"frequency"`
		Amplitude   float64 `json:"amplitude"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Set defaults if not provided
	if request.Frequency <= 0 {
		request.Frequency = 440.0
	}
	if request.Amplitude <= 0 {
		request.Amplitude = 0.3
	}

	// Clamp amplitude to safe range
	if request.Amplitude > 1.0 {
		request.Amplitude = 1.0
	}

	if err := av.startPlayback(request.DeviceIndex, request.Frequency, request.Amplitude); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "playback started"})
}

func (av *AudioVisualizer) handleStopPlayback(w http.ResponseWriter, r *http.Request) {
	if err := av.stopPlayback(); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "playback stopped"})
}

func (av *AudioVisualizer) serveHome(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "static/index.html")
}

func main() {
	visualizer := NewAudioVisualizer()

	if err := visualizer.initPortAudio(); err != nil {
		log.Fatalf("Failed to initialize PortAudio: %v", err)
	}
	defer visualizer.terminate()

	// Setup routes
	r := mux.NewRouter()
	r.HandleFunc("/", visualizer.serveHome)
	r.HandleFunc("/api/data", visualizer.handleAudioData).Methods("GET")
	r.HandleFunc("/api/devices", visualizer.handleDevices).Methods("GET")
	r.HandleFunc("/api/start", visualizer.handleStartRecording).Methods("POST")
	r.HandleFunc("/api/stop", visualizer.handleStopRecording).Methods("POST")
	r.HandleFunc("/api/play", visualizer.handleStartPlayback).Methods("POST")
	r.HandleFunc("/api/stop-play", visualizer.handleStopPlayback).Methods("POST")
	r.PathPrefix("/static/").Handler(http.StripPrefix("/static/", http.FileServer(http.Dir("static/"))))

	log.Println("Server starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", r))
}
