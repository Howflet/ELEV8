class User {
  final int id;
  final String campusID;
  final String password;

  User({
    required this.id,
    required this.campusID,
    required this.password
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      campusID: json['campusID'],
      password: json['password']
    );
  }
}