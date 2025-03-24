#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import PoseStamped, Twist
from sensor_msgs.msg import NavSatFix
from smart_city.msg import PollutionAlert

class DroneController:
    def __init__(self):
        rospy.init_node('drone_controller', anonymous=True)
        
        # Drone state
        self.current_position = (0.0, 0.0)
        self.battery_level = 100
        self.chemical_capacity = 1000  # ml
        
        # Subscribers
        rospy.Subscriber('/pollution_alert', PollutionAlert, self.alert_callback)
        rospy.Subscriber('/drone/position', NavSatFix, self.position_callback)
        
        # Publishers
        self.cmd_vel_pub = rospy.Publisher('/drone/cmd_vel', Twist, queue_size=10)
        self.dispersal_pub = rospy.Publisher('/dispersal/activate', Bool, queue_size=10)
        
        self.rate = rospy.Rate(10)  # 10Hz

    def position_callback(self, msg):
        self.current_position = (msg.latitude, msg.longitude)

    def alert_callback(self, msg):
        rospy.loginfo(f"Received pollution alert at {msg.location}")
        self.deploy_to_location(msg.location, msg.severity)

    def deploy_to_location(self, target_location, severity):
        # Simple PID controller for demonstration
        target_lat, target_lon = target_location
        current_lat, current_lon = self.current_position
        
        while self.calculate_distance(current_lat, current_lon, target_lat, target_lon) > 0.001:
            # Calculate movement commands
            vel_msg = Twist()
            lat_error = target_lat - current_lat
            lon_error = target_lon - current_lon
            
            vel_msg.linear.x = lat_error * 0.5
            vel_msg.linear.y = lon_error * 0.5
            
            self.cmd_vel_pub.publish(vel_msg)
            self.rate.sleep()
            
            # Update position (simulated)
            current_lat += vel_msg.linear.x * 0.1
            current_lon += vel_msg.linear.y * 0.1

        self.activate_dispersal(severity)

    def activate_dispersal(self, severity):
        dispersal_rate = min(severity * 10, 100)  # ml/s
        duration = min(self.chemical_capacity / dispersal_rate, 30)  # max 30s
        
        rospy.loginfo(f"Activating dispersal at {dispersal_rate}ml/s for {duration}s")
        
        start_time = rospy.Time.now()
        while (rospy.Time.now() - start_time).to_sec() < duration:
            self.dispersal_pub.publish(True)
            self.chemical_capacity -= dispersal_rate * 0.1
            self.rate.sleep()
        
        self.dispersal_pub.publish(False)

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        # Simplified distance calculation
        return ((lat2-lat1)**2 + (lon2-lon1)**2)**0.5

if __name__ == '__main__':
    try:
        controller = DroneController()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
