import os
from flask_restplus import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from config import MODEL_META_DATA
from core.backend import ModelWrapper


UPLOAD_FOLDER = './assets'


api = Namespace('model', description='Model information and inference operations')

model_meta = api.model('ModelMetadata', {
    'id': fields.String(required=True, description='Model identifier'),
    'name': fields.String(required=True, description='Model name'),
    'description': fields.String(required=True, description='Model description'),
    'type': fields.String(required=True, description='Model type'),
    'license': fields.String(required=False, description='Model license')
})


@api.route('/metadata')
class Model(Resource):
    @api.doc('get_metadata')
    @api.marshal_with(model_meta)
    def get(self):
        """Return the metadata associated with the model"""
        return MODEL_META_DATA


label_prediction = api.model('LabelPrediction', {
    'label_id': fields.String(required=False, description='Class label identifier'),
    'label': fields.String(required=True, description='Class label'),
    'probability': fields.Float(required=True)
})

predict_response = api.model('ModelPredictResponse', {
    'status': fields.String(required=True, description='Response status message'),
    'predictions': fields.List(fields.Nested(label_prediction), description='Predicted labels and probabilities')
})

# set up parser for image input data
video_parser = api.parser()
video_parser.add_argument('video', type=FileStorage, location='files', required=True,
                          help="MPEG-4 video file to run predictions on")


@api.route('/predict')
class Predict(Resource):

    model_wrapper = ModelWrapper()

    @api.doc('predict')
    @api.expect(video_parser)
    @api.marshal_with(predict_response)
    def post(self):
        """Make a prediction given input data"""
        result = {'status': 'error'}

        #  Take video save it into directory
        args = video_parser.parse_args()
        video_data = args['video']
        filepath = os.path.join(UPLOAD_FOLDER, video_data.filename)
        video_data.save(filepath)

        #  Run predict function on file

        preds = self.model_wrapper.predict(filepath)
        label_preds = [{'label_id': p[0], 'label': p[1], 'probability': p[2]} for p in [x for x in preds]]
        result['predictions'] = label_preds
        result['status'] = 'ok'

        return result
