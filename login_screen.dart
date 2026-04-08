import 'package:flutter/material.dart';
import '../service/api_service.dart';
import '../models/user_model.dart';


class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

// Building the Login Screen
class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _campusIDController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  

  @override
  void dispose() {
    _campusIDController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
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
              // Creating Campus ID Text Box
              // Creating space between Heading and GSU ID Text Box (vertically)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 30),
                  child: Form(
                    child: Column(
                      children: [
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 35),
                          child: TextFormField(
                            decoration: InputDecoration(
                              labelText: "Campus ID",
                              hintText: "Enter Campus ID",
                              border: OutlineInputBorder()
                            ),
                            controller: _campusIDController,
                            onChanged: (String value) {
                                            
                            },
                            // If the text box is empty, it will send a message to the user
                            validator: (value) {
                              return value!.isEmpty ? "Please enter Campus ID": null;
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
                            controller: _passwordController,
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
                            onPressed: () async {
                              final response = await ApiService.login(_campusIDController.text, _passwordController.text);

                              if (!context.mounted) return;

                              if (response['status'] == 'success') {
                                final user = User.fromJson(response['user']);
                              } else {
                                showDialog(
                                  context: context,
                                  builder: (context) => AlertDialog(
                                    title: Text("Failed Login Attempt"),
                                    content: Text("Incorrect campusID or password."),
                                    actions: [
                                      TextButton(
                                        onPressed: () {
                                          Navigator.pop(context);
                                        },
                                        child: Text("OK")
                                      )
                                    ]));
                              }
                            },
                            color: Colors.blue,
                            textColor: Colors.white,
                            child: Text("Login")
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
          ], // Text Widgets
        ),
    );
  }
}