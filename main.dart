import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

// Starting the App
void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  _MyAppState createState() => _MyAppState();
}

// Building the App
class _MyAppState extends State<MyApp> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _campusIDController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _campusIDController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin(BuildContext scaffoldContext) async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final response = await http.post(
        Uri.parse('http://localhost:5000/api/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'campusID': _campusIDController.text,
          'password': _passwordController.text,
        }),
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['status'] == 'success') {
        ScaffoldMessenger.of(scaffoldContext).showSnackBar(
          SnackBar(
            content: Text('Login successful! Access Level: ${responseData['user']['accessLevel']}'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        ScaffoldMessenger.of(scaffoldContext).showSnackBar(
          SnackBar(
            content: Text(responseData['message'] ?? 'Login failed'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(scaffoldContext).showSnackBar(
        SnackBar(
          content: Text('Connection error: Could not reach server'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Builder(
        builder: (scaffoldContext) => Scaffold(
          appBar: AppBar(
            title: Text("Elev8 Login Screen"),
          ),
          body: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(
                "Login",
                style: TextStyle(
                    fontSize: 35,
                    color: Colors.blue,
                    fontWeight: FontWeight.bold),
              ),
              // Creating GSU ID Text Box
              // Creating space between Heading and GSU ID Text Box (vertically)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 30),
                child: Form(
                  key: _formKey,
                  child: Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 35),
                        child: TextFormField(
                          controller: _campusIDController,
                          keyboardType: TextInputType.number,
                          decoration: InputDecoration(
                              labelText: "GSU ID",
                              hintText: "Enter GSU ID",
                              prefixIcon: Icon(Icons.numbers),
                              border: OutlineInputBorder()),
                          // If the text box is empty, it will send a message to the user
                          validator: (value) {
                            return value!.isEmpty
                                ? "Please enter GSU ID"
                                : null;
                          },
                        ),
                      ),

                      // Add space between the text boxes (vertically)
                      SizedBox(height: 30),

                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 35),
                        child: TextFormField(
                          controller: _passwordController,
                          keyboardType: TextInputType.visiblePassword,
                          obscureText: true,
                          decoration: InputDecoration(
                              labelText: "Password",
                              hintText: "Enter Password",
                              prefixIcon: Icon(Icons.password),
                              border: OutlineInputBorder()),
                          // If the text box is empty, it will send a message to the user
                          validator: (value) {
                            if (value!.isEmpty) {
                              return "Please enter password";
                            }
                            if (value.length < 8) {
                              return "Password must be at least 8 characters";
                            }
                            return null;
                          },
                        ),
                      ),

                      SizedBox(height: 30),

                      // Creating Login Button
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 35),
                        child: _isLoading
                            ? CircularProgressIndicator()
                            : MaterialButton(
                                minWidth: double.infinity,
                                onPressed: () => _handleLogin(scaffoldContext),
                                child: Text("Login"),
                                color: Colors.blue,
                                textColor: Colors.white,
                              ),
                      ),
                    ],
                  ),
                ),
              ),
            ], // Text Widgets
          ),
        ),
      ),
    );
  }
}