class FolderWatch {
  Future<void> start(String path, Future<void> Function(String, List<int>, String) upload, void Function(String) report) async {}
  void stop() {}
}
