
// FaceAnalytics.jsx
import { Card, CardBody, CardHeader } from "@nextui-org/react";
import { Progress } from "@nextui-org/react";
import { Users, Brain, Clock } from "lucide-react";

export const FaceAnalytics = ({ faceStats }) => {
    if (!faceStats) return null;

    const totalPeople = faceStats.gender_counts.Man + faceStats.gender_counts.Woman;
    const totalEmotions = Object.values(faceStats.emotion_counts).reduce((a, b) => a + b, 0);

    const emotionColors = {
        happy: "success",
        neutral: "default",
        sad: "secondary",
        angry: "warning",
        fear: "danger"
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Age Stats */}
            <Card className="w-full">
                <CardHeader className="flex flex-row items-center gap-4">
                    <Clock className="w-6 h-6" aria-hidden="true" />
                    <h3 className="text-lg font-semibold">Age Distribution</h3>
                </CardHeader>
                <CardBody className="pt-0">
                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between mb-2">
                                <span className="text-sm">Average Age</span>
                                <span className="font-semibold">{faceStats?.age?.average?.toFixed(1)}</span>
                            </div>
                            <Progress 
                                aria-label="Average age progress"
                                value={faceStats?.age.average} 
                                max={100} 
                                className="h-2" 
                            />
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Range: {faceStats?.age.min} - {faceStats?.age.max} years</span>
                        </div>
                    </div>
                </CardBody>
            </Card>

            {/* Gender Distribution */}
            <Card className="w-full">
                <CardHeader className="flex flex-row items-center gap-4">
                    <Users className="w-6 h-6" aria-hidden="true" />
                    <h3 className="text-lg font-semibold">Gender Distribution</h3>
                </CardHeader>
                <CardBody className="pt-0">
                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between mb-2">
                                <span className="text-sm">Men</span>
                                <span className="font-semibold">
                                    {((faceStats.gender_counts.Man / totalPeople) * 100).toFixed(1)}%
                                </span>
                            </div>
                            <Progress 
                                aria-label="Men percentage"
                                value={(faceStats.gender_counts.Man / totalPeople) * 100} 
                                className="h-2" 
                            />
                        </div>
                        <div>
                            <div className="flex justify-between mb-2">
                                <span className="text-sm">Women</span>
                                <span className="font-semibold">
                                    {((faceStats.gender_counts.Woman / totalPeople) * 100).toFixed(1)}%
                                </span>
                            </div>
                            <Progress 
                                aria-label="Women percentage"
                                value={(faceStats.gender_counts.Woman / totalPeople) * 100} 
                                className="h-2" 
                            />
                        </div>
                        <div className="text-sm text-gray-500">
                            Total Analytics: {totalPeople}
                        </div>
                    </div>
                </CardBody>
            </Card>

            {/* Emotion Distribution */}
            <Card className="w-full">
                <CardHeader className="flex flex-row items-center gap-4">
                    <Brain className="w-6 h-6" aria-hidden="true" />
                    <h3 className="text-lg font-semibold">Emotion Analysis</h3>
                </CardHeader>
                <CardBody className="pt-0">
                    <div className="space-y-4">
                        {Object.entries(faceStats.emotion_counts).map(([emotion, count]) => (
                            <div key={emotion}>
                                <div className="flex justify-between mb-2">
                                    <span className="text-sm capitalize">{emotion}</span>
                                    <span className="font-semibold">
                                        {((count / totalEmotions) * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <Progress
                                    aria-label={`${emotion} percentage`}
                                    value={(count / totalEmotions) * 100}
                                    className="h-2"
                                    color={emotionColors[emotion]}
                                />
                            </div>
                        ))}
                    </div>
                </CardBody>
            </Card>
        </div>
    );
};