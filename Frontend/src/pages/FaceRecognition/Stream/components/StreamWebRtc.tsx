


import React, { useEffect, useRef, useState } from "react";
import { Progress } from "@nextui-org/react";
import adapter from "webrtc-adapter";
import Janus from "janus-gateway";

// Initialize adapter globally
if (typeof window !== 'undefined') {
  window.adapter = adapter;
}

// TURN server configuration
const getIceServers = () => {
  const hostname = window.location.hostname;
  
  return [
    {
      urls: `turn:${hostname}:30478`,
      username: "admin",
      credential: "admin",
      credentialType: "password"
    },
    {
      urls: `stun:${hostname}:30478`
    }
  ];
};

const StreamWebRtc = ({ id }) => {
  const videoRef = useRef(null);
  let janusInstance = null;
  let streamingPlugin = null;
  const [loading, setLoading] = useState(true);
  const [hidden, setHidden] = useState("hidden");
  const [error, setError] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("Initializing...");
  const [progress, setProgress] = useState(0);

  // ADDED: Better video play function
  const playVideo = async (videoElement) => {
    if (!videoElement) return;
    
    try {
      console.log("🎬 Attempting to play video...");
      
      // Ensure video is configured for autoplay
      videoElement.muted = true;
      videoElement.playsInline = true;
      
      await videoElement.play();
      
      setLoading(false);
      setHidden("");
      updateProgress("Video playing");
      console.log("✅ Video playing successfully!");
      
    } catch (error) {
      console.warn("⚠️ Video play failed:", error.message);
      
      // Retry for AbortError
      if (error.name === 'AbortError') {
        setTimeout(async () => {
          try {
            await videoElement.play();
            setLoading(false);
            setHidden("");
            updateProgress("Video playing");
            console.log("✅ Video playing after retry!");
          } catch (retryError) {
            console.error("❌ Video retry failed:", retryError.message);
          }
        }, 100);
      }
    }
  };

  // ADDED: Click handler for manual play
  const handleVideoClick = () => {
    if (videoRef.current && videoRef.current.paused) {
      console.log("🖱️ User clicked video, attempting to play...");
      playVideo(videoRef.current);
    }
  };

  const updateProgress = (status) => {
    setLoadingStatus(status);
    switch (status) {
      case "Initializing Janus...":
        setProgress(10);
        break;
      case "Connecting to Janus server...":
        setProgress(30);
        break;
      case "Attaching to streaming plugin...":
        setProgress(50);
        break;
      case "Requesting stream...":
        setProgress(60);
        break;
      case "Stream is starting...":
        setProgress(70);
        break;
      case "Stream started, waiting for video...":
        setProgress(80);
        break;
      case "Creating WebRTC answer...":
        setProgress(90);
        break;
      case "Video playing":
        setProgress(100);
        break;
      default:
        break;
    }
  };

  useEffect(() => {
    const initJanus = () => {
      updateProgress("Initializing Janus...");
      console.log("Initializing Janus...");

      if (typeof Janus === 'undefined') {
        console.error("Janus not loaded");
        setError(true);
        setLoading(false);
        return;
      }

      const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
      const hostname = window.location.hostname;
      const janusUrl = `${protocol}://${hostname}:30088/janus`;
      
      console.log(`Connecting to Janus at: ${janusUrl}`);
      
      Janus.init({
        debug: false,
        callback: () => {
          updateProgress("Connecting to Janus server...");
          console.log("Connecting to Janus server...");
          janusInstance = new Janus({
            server: janusUrl,
            iceServers: getIceServers(),
            ipv6: false,
            withCredentials: false,
            max_poll_events: 10,
            success: () => {
              updateProgress("Attaching to streaming plugin...");
              console.log("Attaching to streaming plugin...");
              janusInstance.attach({
                plugin: "janus.plugin.streaming",
                success: (pluginHandle) => {
                  streamingPlugin = pluginHandle;
                  updateProgress("Requesting stream...");
                  console.log("------> ", id, " <------");
                  console.log("Requesting stream...");
                  const body = { request: "watch", id: parseInt(id.toString()) };
                  streamingPlugin.send({ message: body });
                  console.log("Stream request sent:", body);
                },
                error: (error) => {
                  console.error("Error attaching plugin:", error);
                  setError(true);
                  setLoading(false);
                },
                onmessage: (msg, jsep) => {
                  console.log("Received message:", msg);
                  try {
                    if (msg.result?.status === "starting") {
                      updateProgress("Stream is starting...");
                      console.log("Stream is starting...");
                    } else if (msg.result?.status === "started") {
                      updateProgress("Stream started, waiting for video...");
                      console.log("Stream started, waiting for video...");
                    }
                  } catch (e) {
                    console.log("Error in onmessage", e);
                    setHidden("hidden");
                    setLoading(false);
                    setError(true);
                  }
                  if (jsep !== undefined && jsep !== null) {
                    updateProgress("Creating WebRTC answer...");
                    console.log("Creating WebRTC answer...");
                    streamingPlugin.createAnswer({
                      jsep: jsep,
                      media: {
                        audioSend: false,
                        videoSend: false,
                        audioRecv: true,
                        videoRecv: true
                      },
                      iceRestart: true,
                      success: (jsep) => {
                        updateProgress("Starting stream...");
                        console.log("Starting stream...");
                        const body = { request: "start" };
                        streamingPlugin.send({ message: body, jsep: jsep });
                      },
                      error: (error) => {
                        console.error("Error creating WebRTC answer:", error);
                      },
                    });
                  }
                },
                // IMPROVED: Better onremotestream handling
                onremotestream: (stream) => {
                  console.log("🎥 Received remote stream:", stream);
                  console.log("🔍 Stream tracks:", stream.getTracks().map(t => `${t.kind}: ${t.readyState}`));
                  
                  if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    
                    // CHANGED: Use improved play function
                    playVideo(videoRef.current);
                  }
                },
                onicecandidate: (candidate) => {
                  if (candidate) {
                    console.log("Received ICE candidate:", candidate);
                  }
                },
                // IMPROVED: Better onremotetrack handling
                onremotetrack: (track, mid, on) => {
                  console.log("🎵 Remote track received:", track.kind, "MID:", mid, "ON:", on);
                  
                  if (videoRef.current && on) {
                    let stream = videoRef.current.srcObject || new MediaStream();
                    
                    // Remove existing track of same kind
                    const existingTrack = stream.getTracks().find(t => t.kind === track.kind);
                    if (existingTrack) {
                      stream.removeTrack(existingTrack);
                      console.log(`🗑️ Removed existing ${track.kind} track`);
                    }
                    
                    stream.addTrack(track);
                    videoRef.current.srcObject = stream;
                    
                    console.log(`✅ Added ${track.kind} track. Stream now has: ${stream.getTracks().map(t => t.kind).join(', ')}`);
                    
                    // Force video refresh and try to play
                    videoRef.current.load();
                    
                    // CHANGED: Use improved play function
                    setTimeout(() => {
                      playVideo(videoRef.current);
                    }, 100);
                  }
                },
                oncleanup: () => {
                  console.log("Janus cleanup");
                  setHidden("");
                },
                onlocaltrack: (track) => {
                  console.log("Local track:", track);
                  setHidden("hidden");
                  setLoading(false);
                  setError(true);
                },
              });
            },
            error: (error) => {
              console.error("Janus error:", error);
              setHidden("hidden");
              setLoading(false);
              setError(true);
            },
            destroyed: () => {
              console.log("Janus session destroyed");
              setHidden("hidden");
              setLoading(false);
              setError(true);
            },
          });
        },
      });
    };

    initJanus();

    if (videoRef.current) {
      videoRef.current.addEventListener("loadedmetadata", () => {
        console.log("📐 Video metadata loaded:", videoRef.current.videoWidth, videoRef.current.videoHeight);
        setHidden("");
        setLoading(false);
      });
      
      // ADDED: Additional event listeners for debugging
      videoRef.current.addEventListener("canplay", () => {
        console.log("🎬 Video can play");
      });
      
      videoRef.current.addEventListener("playing", () => {
        console.log("✅ Video is playing");
      });
      
      videoRef.current.addEventListener("error", (e) => {
        console.error("❌ Video error:", e.target.error);
      });
    }

    return () => {
      if (streamingPlugin) {
        const body = { request: "stop" };
        streamingPlugin.send({ message: body });
        streamingPlugin.detach();
        setHidden("hidden");
        setLoading(false);
        setError(true);
        videoRef.current = null;
      }

      if (janusInstance) {
        janusInstance.destroy();
      }
    };
  }, [id]);

  return (
    <>
      <div className={`${hidden} flex gap-4 w-full min-h-72 min-w-72 items-center justify-center`}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          controls
          muted
          onClick={handleVideoClick} // ADDED: Click handler
          className="w-full h-full object-contain cursor-pointer border-2 border-gray-300 rounded" // ADDED: Visual feedback
          aria-label="Live Stream Video"
          style={{ backgroundColor: '#000' }} // ADDED: Black background
        />
      </div>
      {loading && (
        <div className="flex flex-col gap-4 w-full min-h-72 min-w-72 items-center justify-center p-4">
          <Progress
            value={progress}
            color="primary"
            size="md"
            className="w-full max-w-md"
            showValueLabel={true}
          />
          <p className="text-sm text-gray-500">{loadingStatus}</p>
          {/* ADDED: User instruction */}
          {progress >= 80 && (
            <p className="text-xs text-blue-600">💡 Click the video if it doesn't start automatically</p>
          )}
        </div>
      )}
      {error && (
        <div className="flex gap-4 w-full min-h-72 min-w-72 items-center justify-center">
          <h1 className="text-red-500">Error in streaming</h1>
        </div>
      )}
    </>
  );
};

export default StreamWebRtc;