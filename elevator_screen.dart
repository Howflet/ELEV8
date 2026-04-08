import 'package:flutter/material.dart';
import '../service/api_service.dart';
import '../screens/login_screen.dart';

class ElevatorScreen extends StatefulWidget {
  const ElevatorScreen({super.key});

  @override
  _ElevatorScreenState createState() => _ElevatorScreenState();
}

// Building Elevator Screen

class _ElevatorScreenState extends State<ElevatorScreen> {

  // Elevator's Current Floor
  int currentFloor = 1;

  // User inputting their current floor and destination floor
  final TextEditingController _currentFloorController = TextEditingController();
  final TextEditingController _destFloorController = TextEditingController();

  @override
  void initState() {
    super.initState();
    loadElevator(currentFloor,currentFloor);
  }

  void loadElevator(int current, int dest) async {
    final elevatorData = await ApiService.elevator(current, dest);

    setState(() {
      currentFloor = elevatorData['current_floor']; // What the API returns
    });
  }

  void checkFloor(int current, int dest) {
    if (current == dest) {
      showDialog(
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            title: Text("Floor Selection Error"),
            content: Text('The current floor and destination floor cannot be the same!'),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: Text('OK'))
            ]
          );
        }
      );
    } else {
      loadElevator(current, dest);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
      title: Text("Elevator"),
        ),
        body: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [

            // Display Current Floor
            Text("Current Floor: $currentFloor"),
            const SizedBox(height: 30),    
            
            TextField(
              controller: _currentFloorController,
              decoration: InputDecoration(labelText: "Current Floor"),
              keyboardType: TextInputType.number),
            
            // Display Destination Floor
            Text("Destination Floor"),
            const SizedBox(height: 30),

            TextField(
              controller: _destFloorController,
              decoration: InputDecoration(labelText: "Destination Floor"),
              keyboardType: TextInputType.number),
            
        
            // Create Sumbit Button
            ElevatedButton(
                  onPressed: () {
                    int current = int.tryParse(_currentFloorController.text) ?? 1;
                    int dest = int.tryParse(_destFloorController.text) ?? 1;
                    
                    checkFloor(current,dest);
                  },
                  child: Text("Submit Request")),

            const SizedBox(height:30),

            ElevatedButton(
              onPressed: () {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (context) => LoginScreen()));
              },
              child: Text("Logout"))
          ]
        ));}}