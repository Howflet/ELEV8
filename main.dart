import 'package:flutter/material.dart';

// Starting the App
void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({Key? key}): super(key: key);

  @override
  _MyAppState createState() => _MyAppState();
}

// Building the App
class _MyAppState extends State<MyApp> {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(
          title: Text("Elev8 Login Screen"),
        ),
        body: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text("Login",
                  style: TextStyle(
                    fontSize: 35,
                    color: Colors.blue,
                    fontWeight: FontWeight.bold
                  ),
                ),
              // Creating GSU ID Text Box
              // Creating space between Heading and GSU ID Text Box (vertically)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 30),
                  child: Form(
                    child: Column(
                      children: [
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 35),
                          child: TextFormField(
                            keyboardType: TextInputType.number,
                            decoration: InputDecoration(
                              labelText: "GSU ID",
                              hintText: "Enter GSU ID",
                              prefixIcon: Icon(Icons.numbers),
                              border: OutlineInputBorder()
                            ),
                            onChanged: (String value) {
                                            
                            },
                            // If the text box is empty, it will send a message to the user
                            validator: (value) {
                              return value!.isEmpty ? "Please enter GSU ID": null;
                            }
                          ),
                        ),
                  
                        // Add space between the text boxes (vertically)
                        SizedBox(height:30),
                  
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 35),
                          child: TextFormField(
                            keyboardType: TextInputType.visiblePassword,
                            decoration: InputDecoration(
                              labelText: "Password",
                              hintText: "Enter Password",
                              prefixIcon: Icon(Icons.password),
                              border: OutlineInputBorder()
                            ),
                            onChanged: (String value) {
                                            
                            },
                            // If the text box is empty, it will send a message to the user
                            validator: (value) {
                              return value!.isEmpty ? "Please enter password": null;
                            }
                          ),
                        ),

                        SizedBox(height:30),

                        // Creating Login Button
                        Padding(
                          padding: const EdgeInsetsGeometry.symmetric(horizontal: 35),
                          child: MaterialButton(
                            minWidth: double.infinity,
                            onPressed: () {},
                            child: Text("Login"),
                            color: Colors.blue,
                            textColor: Colors.white
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
          ], // Text Widgets
        ),
      ),
    );
  }
}